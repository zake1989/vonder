import sys
from tree_sitter import Language, Parser
import tree_sitter_swift as tsp_swift

from method_generator import generate_method

import json
import random
import string


# =====================
# 加载 Bool 名称池
# =====================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

variable_names_pool = config.get("bool_names", [])

def random_suffix():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(3, 6)))

def generate_variable_name():
    return random.choice(variable_names_pool) + random_suffix().capitalize()

def generate_bool_declarations(count=1):
    return [f"    var {generate_variable_name()}: Bool = {random.choice(['true','false'])}" for _ in range(count)]

def extract_function_name(func_node, source_bytes):
    # func_node 是 function_declaration 类型节点
    for child in func_node.children:
        if child.type == "simple_identifier":
            return source_bytes[child.start_byte:child.end_byte].decode('utf-8')
    return "unknown_func"

# =====================
# Tree-sitter helpers
# =====================

def find_class_nodes(node, results=None):
    if results is None:
        results = []
    if node.type == "class_declaration":
        results.append(node)
    for child in node.children:
        find_class_nodes(child, results)
    return results

def find_functions(node, results):
    if node.type == 'function_declaration':
        results.append(node)
    for child in node.children:
        find_functions(child, results)

def find_and_rebuild_parameters(node, source_code_bytes):
    start_paren = end_paren = None
    for child in node.children:
        if child.type == '(' and start_paren is None:
            start_paren = child
        if child.type == ')':
            end_paren = child
    if start_paren and end_paren:
        return start_paren, end_paren
    for child in node.children:
        sub_start, sub_end = find_and_rebuild_parameters(child, source_code_bytes)
        if sub_start and sub_end:
            return sub_start, sub_end
    return None, None

def find_class_body_brace_node(class_node):
    for child in class_node.children:
        if child.type == "class_body":
            for grandchild in child.children:
                if grandchild.type == "{":
                    return grandchild
    return None

def find_function_body_brace(func_node):
    for child in func_node.children:
        if child.type == "function_body":
            for grandchild in child.children:
                if grandchild.type == "{":
                    return grandchild
    return None

# =====================
# 插入 class 成员
# =====================

def insert_bool_properties_to_class(tree, source_code_bytes):
    class_bool_map = {}
    classes = find_class_nodes(tree.root_node)
    classes.sort(key=lambda n: n.start_byte, reverse=True)
    output_parts, last_index = [], len(source_code_bytes)

    for cls in classes:
        # 类名
        class_name = "Unknown"
        for child in cls.children:
            if child.type == "type_identifier":
                class_name = source_code_bytes[child.start_byte:child.end_byte].decode('utf-8')
                break

        brace_node = find_class_body_brace_node(cls)
        if not brace_node:
            continue

        insert_pos = brace_node.end_byte
        declarations = generate_bool_declarations(random.randint(1,3))
        bool_var_names = [d.split()[1].rstrip(":") for d in declarations]
        class_bool_map[class_name] = bool_var_names

        insert_text = "\n" + "\n".join(declarations)
        output_parts.append(source_code_bytes[insert_pos:last_index])
        output_parts.append(insert_text.encode('utf-8'))
        last_index = insert_pos

        print(f"✅ 在 class {class_name} 插入 Bool {bool_var_names}")

    output_parts.append(source_code_bytes[:last_index])
    new_source = b"".join(reversed(output_parts))
    return new_source, class_bool_map

# =====================
# 插入 function 参数
# =====================

def insert_parameter_to_functions(tree, source_code_bytes):
    function_bool_map = {}
    functions = []
    find_functions(tree.root_node, functions)
    functions.sort(key=lambda n: n.start_byte, reverse=True)
    output_parts, last_index = [], len(source_code_bytes)

    for func in functions:
        param_bool = generate_variable_name()
        start_paren, end_paren = find_and_rebuild_parameters(func, source_code_bytes)
        if not start_paren or not end_paren:
            continue

        old_params = source_code_bytes[start_paren.start_byte:end_paren.end_byte].decode('utf-8')
        if old_params == '()':
            new_params = f'({param_bool}: Bool = false)'
        else:
            new_params = old_params[:-1] + f', {param_bool}: Bool = false)'

        new_func_code = (
            source_code_bytes[func.start_byte:start_paren.start_byte].decode('utf-8') +
            new_params +
            source_code_bytes[end_paren.end_byte:func.end_byte].decode('utf-8')
        )

        # 找函数所属的类（如果有）
        parent_node = func.parent
        class_name = "Unknown"
        while parent_node:
            if parent_node.type == "class_declaration":
                for child in parent_node.children:
                    if child.type == "type_identifier":
                        class_name = source_code_bytes[child.start_byte:child.end_byte].decode('utf-8')
                        break
                break
            parent_node = parent_node.parent

        # 找函数名
        func_name = "unknown"
        for child in func.children:
            if child.type == "simple_identifier":
                func_name = source_code_bytes[child.start_byte:child.end_byte].decode('utf-8')
                break

        function_bool_map[(class_name, func_name)] = param_bool
        print(f"✅ 在 function {func_name} (class {class_name}) 添加参数 {param_bool}")

        output_parts.append(source_code_bytes[func.end_byte:last_index])
        output_parts.append(new_func_code.encode('utf-8'))
        last_index = func.start_byte

    output_parts.append(source_code_bytes[:last_index])
    new_source = b"".join(reversed(output_parts))
    return new_source, function_bool_map

# =====================
# 插入函数体 if
# =====================

def analyze_function_returns(func_node, source_code_bytes):
    has_arrow = False
    can_be_nil = False

    for idx, child in enumerate(func_node.children):
        if child.type == '->':
            has_arrow = True
            if idx + 1 < len(func_node.children):
                return_node = func_node.children[idx + 1]
                # 判断是否 optional
                if is_optional_node(return_node):
                    can_be_nil = True
            break

    if not has_arrow:
        return "no_return"
    elif can_be_nil:
        return "can_be_nil"
    else:
        return "must_return"

def is_optional_node(node):
    if node.type == "optional_type":
        return True
    for child in node.children:
        if is_optional_node(child):
            return True
    return False

def insert_if_to_functions(tree, source_code_bytes, class_bool_map, function_bool_map):
    functions = []
    find_functions(tree.root_node, functions)
    functions.sort(key=lambda n: n.start_byte, reverse=True)
    output_parts, last_index = [], len(source_code_bytes)

    for func in functions:
        # 查找函数所属类（如果没有，就说明是自由函数）
        parent_class = func
        while parent_class.parent and parent_class.type != "class_declaration":
            parent_class = parent_class.parent

        # 获取类名
        class_name = "Unknown"
        for child in parent_class.children:
            if child.type == "type_identifier":
                class_name = source_code_bytes[child.start_byte:child.end_byte].decode('utf-8')
                break

        # 获取函数名
        func_name = "unknown"
        for child in func.children:
            if child.type == "simple_identifier":
                func_name = source_code_bytes[child.start_byte:child.end_byte].decode('utf-8')
                break

        # 查找参数 bool
        param_bool = function_bool_map.get((class_name, func_name), None)
        if not param_bool:
            continue

        # 查找函数体 brace
        brace_node = find_function_body_brace(func)
        if not brace_node:
            continue

        # 判断函数返回类型
        return_type = analyze_function_returns(func, source_code_bytes)

        # 随机选一个假方法模板
        fake_method_code = generate_method(has_return=False)
        print("=== fake_method_code ===")
        print(fake_method_code)

        SWIFT_LANGUAGE = Language(tsp_swift.language())
        parser = Parser(language=SWIFT_LANGUAGE)

        call_method_tree = parser.parse(fake_method_code.encode('utf-8'))
        call_method_root_node = call_method_tree.root_node
        print("=== Parsed tree root node ===")
        print(f"root_node type: {call_method_root_node.type}, children count: {len(call_method_root_node.children)}")

        need_call_func_name = None
        for child in call_method_root_node.children:
            print(f"child type: {child.type}")
            if child.type == "function_declaration":
                need_call_func_name = extract_function_name(child, fake_method_code.encode('utf-8'))
                print(f"Extracted function name: {need_call_func_name}")

        # 调用假方法
        fake_call = ""
        if need_call_func_name:
            fake_call = f"{need_call_func_name}()"
        else:
            fake_call = ""

        print(f"Fake call string: {fake_call}")

        # 决定插入条件
        member_bools = class_bool_map.get(class_name, [])
        if class_name != "Unknown" and member_bools:
            member_var = random.choice(member_bools)
            condition = f"self.{member_var} && {param_bool}"
            message = f"Both flags are true (self.{member_var} & {param_bool})"
        else:
            condition = f"{param_bool}"
            message = f"{param_bool} is true"

        # 根据返回情况生成插入代码
        if return_type == "no_return":
            insert_logic = f"""
                {fake_method_code}

                if {condition} {{
                    {fake_call}
                    print("{message}")
                    assert({condition})
                    return
                }}
            """
        elif return_type == "can_be_nil":
            insert_logic = f"""
                {fake_method_code}

                if {condition} {{   
                    {fake_call} 
                    print("{message}")
                    assert({condition})
                    return nil
                }}
            """
        else:  # must_return
            insert_logic = f"""
                {fake_method_code}

                defer {{
                    if {condition} {{
                        {fake_call}
                        print("{message}")
                        assert({condition})
                    }}
                }}
            """

        # 生成新函数代码
        insert_pos = brace_node.end_byte
        new_func_code = (
            source_code_bytes[func.start_byte:insert_pos].decode('utf-8') +
            insert_logic +
            source_code_bytes[insert_pos:func.end_byte].decode('utf-8')
        )

        print(f"✅ 在 function {func_name} (class {class_name}) 插入逻辑，使用条件: {condition}")

        output_parts.append(source_code_bytes[func.end_byte:last_index])
        output_parts.append(new_func_code.encode('utf-8'))
        last_index = func.start_byte

    output_parts.append(source_code_bytes[:last_index])
    new_source = b"".join(reversed(output_parts))
    return new_source

# =====================
# 主流程
# =====================

def process_swift_file(source_path):
    source_code = open(source_path, 'rb').read()

    SWIFT_LANGUAGE = Language(tsp_swift.language())
    parser = Parser(language=SWIFT_LANGUAGE)

    # 第一步: 插入 class 成员
    tree = parser.parse(source_code)
    new_source_code, class_bool_map = insert_bool_properties_to_class(tree, source_code)

    # 第二步: 插入 function 参数
    tree = parser.parse(new_source_code)
    new_source_code, function_bool_map = insert_parameter_to_functions(tree, new_source_code)

    # 第三步: 插入函数体 if
    tree = parser.parse(new_source_code)
    new_source_code = insert_if_to_functions(tree, new_source_code, class_bool_map, function_bool_map)

    # print("\n===== 最终修改后的文件内容 =====")
    # print(new_source_code.decode('utf-8'))

    with open(source_path, "wb") as f:
        f.write(new_source_code)

    print(f"✅ 文件已覆盖保存到 {source_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <Swift file>")
        sys.exit(1)

    source_path = sys.argv[1]
    process_swift_file(source_path)








