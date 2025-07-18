from tree_sitter import Language, Parser
import tree_sitter_swift as tsp_swift

from method_generator import generate_method

import sys
import re
import json
import random
import string

# =====================
# 载入配置，变量名池
# =====================

DEBUG = True  # 控制打印输出开关

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

variable_names_pool = config.get("bool_names", [])

def random_suffix():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(3, 6)))

def generate_variable_name():
    return random.choice(variable_names_pool) + random_suffix().capitalize()

def generate_bool_declarations(count=1):
    return [f"    var {generate_variable_name()}: Bool = {random.choice(['true','false'])}" for _ in range(count)]

# =====================
# Tree-sitter 辅助函数
# =====================

def find_class_nodes(node, results=None):
    if results is None:
        results = []
    if node.type == "class_declaration":
        is_class = False
        type_name = "Unknown"
        for child in node.children:
            if child.type == "class":
                is_class = True
            # "extension"
        if is_class:
            results.append(node)
        else:
            if DEBUG: print(f"⚠️ 跳过 class extension")
    for child in node.children:
        find_class_nodes(child, results)
    return results

def find_class_body_brace_node(class_node):
    for child in class_node.children:
        if child.type == "class_body":
            for grandchild in child.children:
                if grandchild.type == "{":
                    return grandchild
    return None

def recursive_find_functions(node, results=None):
    if results is None:
        results = []
    if node.type == "function_declaration":
        # 检查是不是在另一个函数的 function_body 里
        parent = node.parent
        inside_function = False
        while parent is not None:
            if parent.type in ("function_body", "statements"):
                inside_function = True
                break
            parent = parent.parent
        if not inside_function:
            results.append(node)
        else:
            if DEBUG: print(f"⚠️ 跳过局部函数")
    for child in node.children:
        recursive_find_functions(child, results)
    return results

def recursive_find_classes(node, results=None):
    if results is None:
        results = []
    if node.type == "class_declaration":
        results.append(node)
    for child in node.children:
        recursive_find_classes(child, results)
    return results

def get_node_text(source_bytes, node):
    return source_bytes[node.start_byte:node.end_byte].decode('utf-8')

def extract_argument_pairs_from_tree(func_node, source_bytes):
    arg_pairs = []
    seen_params = set()

    for param in (child for child in func_node.children if child.type == "parameter"):
        # 检查 inout
        is_inout = any(
            sub_sub.type == "inout"
            for child in param.children if child.type == "parameter_modifiers"
            for mod in child.children
            for sub_sub in mod.children
        )

        simple_id_nodes = [c for c in param.children if c.type == "simple_identifier"]
        if not simple_id_nodes:
            continue

        # 根据数量和外部名判断
        if len(simple_id_nodes) == 2:
            external = get_node_text(source_bytes, simple_id_nodes[0])
            internal = get_node_text(source_bytes, simple_id_nodes[1])
            call_value = f"&{internal}" if is_inout else internal
            if external == "_":
                call = f"{call_value}"
            else:
                call = f"{external}: {call_value}"
        elif len(simple_id_nodes) == 1:
            name = get_node_text(source_bytes, simple_id_nodes[0])
            call_value = f"&{name}" if is_inout else name
            call = f"{name}: {call_value}"
        else:
            continue

        if call not in seen_params:
            seen_params.add(call)
            arg_pairs.append(call)
    
    return arg_pairs

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

def extract_function_name(func_node, source_bytes):
    # func_node 是 function_declaration 类型节点
    for child in func_node.children:
        if child.type == "simple_identifier":
            return source_bytes[child.start_byte:child.end_byte].decode('utf-8')
    return "unknown_func"

def find_function_body_brace(func_node):
    for child in func_node.children:
        if child.type == "function_body":
            for grandchild in child.children:
                if grandchild.type == "{":
                    return grandchild
    return None

# =====================
# 插入 class Bool 成员变量
# =====================

def insert_bool_properties_to_class(tree, source_code_bytes):
    class_bool_map = {}
    classes = find_class_nodes(tree.root_node)
    classes.sort(key=lambda n: n.start_byte, reverse=True)
    output_parts, last_index = [], len(source_code_bytes)

    def get_full_class_name(node):
        names = []
        current = node
        while current:
            if current.type in ("class_declaration", "struct_declaration", "extension_declaration"):
                for c in current.children:
                    if c.type == "type_identifier":
                        names.append(get_node_text(source_code_bytes, c))
                        break
            current = current.parent
        names.reverse()
        return ".".join(names) if names else "Unknown"

    for cls in classes:
        class_name = get_full_class_name(cls)

        brace_node = find_class_body_brace_node(cls)
        if not brace_node:
            continue

        insert_pos = brace_node.end_byte
        declarations = generate_bool_declarations(random.randint(1, 3))
        bool_var_names = [d.split()[1].rstrip(":") for d in declarations]
        class_bool_map[class_name] = bool_var_names

        insert_text = "\n" + "\n".join(declarations)
        output_parts.append(source_code_bytes[insert_pos:last_index])
        output_parts.append(insert_text.encode('utf-8'))
        last_index = insert_pos

        if DEBUG: print(f"✅ 在 class {class_name} 插入 Bool {bool_var_names}")

    output_parts.append(source_code_bytes[:last_index])
    new_source = b"".join(reversed(output_parts))
    return new_source, class_bool_map

# =====================
# 复制函数并添加 bool 参数
# =====================

def get_signature_string(func_node, source_bytes):
    # 找参数括号节点
    start_paren, end_paren = find_and_rebuild_parameters(func_node, source_bytes)
    if not start_paren or not end_paren:
        if DEBUG: print(f"⚠️ 未找到参数括号，跳过函数 {original_name}")
        return ""

    old_params = source_bytes[start_paren.start_byte:end_paren.end_byte].decode('utf-8')
    prefix = source_bytes[func_node.start_byte:start_paren.start_byte].decode('utf-8')

    return prefix + old_params

def extract_function_info(func_node, source_bytes):
    """
    提取函数信息，包括：
    - name: 函数名称
    - signature: 方法签名（包含参数）
    - header: 到 { 的部分（用于显示）
    - body: 函数体 {...}
    - full_code: 整个函数代码
    - start_byte, end_byte: 位置
    - class_name: 所属的 class / struct / extension 名称
    """
    info = {
        "name": None,
        "params": None,
        "return_type": None,
        "header": None,
        "body": None,
        "full_code": None,
        "start_byte": func_node.start_byte,
        "end_byte": func_node.end_byte,
        "func_node": func_node,
        "class_name": "Unknown"
    }

    # 提取函数名、body
    for child in func_node.children:
        if child.type == "simple_identifier":
            info["name"] = get_node_text(source_bytes, child)
        if child.type == "function_body":
            info["body"] = get_node_text(source_bytes, child)

    # 提取 signature
    info["signature"] = get_signature_string(func_node, source_bytes)

    # 提取 header（到 {）
    func_code = get_node_text(source_bytes, func_node)
    brace_pos = func_code.find("{")
    info["header"] = func_code[:brace_pos].strip() if brace_pos > -1 else func_code.strip()

    info["full_code"] = func_code

    # ✅ 支持完整嵌套路径 class/struct/extension/enum，例如 A.B.C
    parent = func_node
    type_stack = []

    while parent is not None:
        if parent.type in ("class_declaration", "struct_declaration", "extension_declaration", "enum_declaration"):
            type_name = None
            for c in parent.children:
                if c.type == "type_identifier":
                    type_name = get_node_text(source_bytes, c)
                    break
                elif c.type == "user_type":
                    for g in c.children:
                        if g.type == "type_identifier":
                            type_name = get_node_text(source_bytes, g)
                            break
            if type_name:
                type_stack.append(type_name)
        parent = parent.parent

    type_stack.reverse()
    info["class_name"] = ".".join(type_stack) if type_stack else "Unknown"

    if DEBUG: print(f"🔍 函数 {info['name']} 属于类型 {info['class_name']}")
    return info

def generate_copied_functions(tree, source_code_bytes):
    function_nodes = recursive_find_functions(tree.root_node)
    function_nodes.sort(key=lambda n: n.start_byte)  # 顺序处理

    function_map = []

    for func in function_nodes:
        info = extract_function_info(func, source_code_bytes)
        original_name = info["name"]
        original_signature = info.get("signature", "")
        if original_name is None:
            continue

        new_name = original_name + random_suffix().capitalize()
        bool_param = generate_variable_name()

        # 找参数括号节点
        start_paren, end_paren = find_and_rebuild_parameters(func, source_code_bytes)
        if not start_paren or not end_paren:
            if DEBUG: print(f"⚠️ 未找到参数括号，跳过函数 {original_name}")
            continue

        old_params = source_code_bytes[start_paren.start_byte:end_paren.end_byte].decode('utf-8')
        if old_params == '()':
            new_params = f'({bool_param}: Bool = false)'
        else:
            new_params = old_params[:-1] + f', {bool_param}: Bool = false)'

        prefix = source_code_bytes[func.start_byte:start_paren.start_byte].decode('utf-8')

        # 去除 override 关键字
        prefix_no_override = re.sub(r'\boverride\s+', '', prefix)

        # 替换函数名（只替换第一个匹配）
        copied_signature = re.sub(r'\b' + re.escape(original_name) + r'\b', new_name, prefix_no_override, count=1) + new_params
        # copied_signature = copied_signature.replace(" ", "")

        body = source_code_bytes[end_paren.end_byte:func.end_byte].decode('utf-8')

        start_line_start = source_code_bytes.rfind(b'\n', 0, func.start_byte) + 1
        line_indent = source_code_bytes[start_line_start:func.start_byte].decode('utf-8')
        if not line_indent.strip():
            indent = line_indent
        else:
            indent = ""

        new_func_code = indent + copied_signature + body

        # ➡️ 查找父类名 (支持 class / struct / extension)
        parent = func
        type_stack = []

        while parent is not None:
            if parent.type in ("class_declaration", "struct_declaration", "extension_declaration", "enum_declaration"):
                type_name = None
                for c in parent.children:
                    if c.type == "type_identifier":
                        type_name = get_node_text(source_code_bytes, c)
                        break
                    elif c.type == "user_type":
                        for g in c.children:
                            if g.type == "type_identifier":
                                type_name = get_node_text(source_code_bytes, g)
                                break
                if type_name:
                    type_stack.append(type_name)
            parent = parent.parent

        type_stack.reverse()
        class_path = ".".join(type_stack) if type_stack else "Unknown"

        # 保存信息
        function_map.append({
            "original_name": original_name,
            "new_name": new_name,
            "bool_param": bool_param,
            "original_signature": original_signature,
            "copied_signature": copied_signature,
            "new_func_code": new_func_code,
            "func_node": func,
            "class_name": class_path  # ✅ 新增
        })

        if DEBUG: print(f"✅ 复制函数 {original_name} -> {new_name}，添加参数 {bool_param}\n原签名:\n{original_signature}\n复制签名:\n{copied_signature}\n")

    return function_map

def insert_copied_functions_after_originals(source_bytes, function_map):
    output_parts = []
    last_index = len(source_bytes)

    # 倒序处理避免插入位置偏移
    for record in sorted(function_map, key=lambda r: r["func_node"].end_byte, reverse=True):
        insert_pos = record["func_node"].end_byte
        copied_code = "\n\n" + record["new_func_code"]

        output_parts.append(source_bytes[insert_pos:last_index])
        output_parts.append(copied_code.encode('utf-8'))
        last_index = insert_pos

    output_parts.append(source_bytes[:last_index])
    return b"".join(reversed(output_parts))

# =====================
# 改写原函数调用复制函数
# =====================

def has_throws_on_function(func_node, source_bytes):
    """
    检查 function_declaration 是否带 throws。
    只在 simple_identifier 到 function_body 之间寻找 throws 节点。
    包含两种情况：
    - throws 节点
    - user_type -> type_identifier == 'throws'
    """
    seen_name = False
    for child in func_node.children:
        if not seen_name:
            if child.type == "simple_identifier":
                seen_name = True
            continue
        if child.type == "function_body":
            break
        if child.type == "throws":
            return True
        if child.type == "user_type":
            # 遍历 user_type 的子节点，找 type_identifier
            for gchild in child.children:
                if gchild.type == "type_identifier":
                    text = get_node_text(source_bytes, gchild)
                    if text == "throws":
                        return True
    return False

def rewrite_single_function_body(source_bytes, func_node, record):
    """
    对单个 function_node 使用 record 重写函数体，并返回新的 bytes。
    """
    new_name = record["new_name"]
    bool_param = record["bool_param"]
    signature = record["original_signature"]

    has_return_type = any(child.type == '->' for child in func_node.children)
    if DEBUG: print(f"🔎 函数 {signature} 是否有返回值: {has_return_type}")

    has_throws = has_throws_on_function(func_node, source_bytes)
    if DEBUG: print(f"🔎 函数 {signature} 是否有错误抛出: {has_throws}")

    arg_pairs = extract_argument_pairs_from_tree(func_node, source_bytes)
    if DEBUG: print(f"📌 提取到的参数对: {arg_pairs}")
    call_args = ", ".join(arg_pairs)
    if call_args:
        call_args += f", {bool_param}: false"
    else:
        call_args = f"{bool_param}: false"
    if DEBUG: print(f"🚀 重组调用参数为: {call_args}")

    body_node = next((c for c in func_node.children if c.type == "function_body"), None)
    if not body_node:
        if DEBUG: print(f"⚠️ 未找到 {signature} 的 function_body，跳过改写")
        return source_bytes  # 返回原始

    # 获取缩进
    line_start = source_bytes.rfind(b'\n', 0, body_node.start_byte) + 1
    line = source_bytes[line_start:body_node.start_byte].decode('utf-8')
    indent_match = re.match(r'\s*', line)
    indent = indent_match.group(0) if indent_match else ""
    if DEBUG: print(f"📝 检测到缩进: '{indent}'")

    # 构造新的函数体
    if has_throws:
        call_line = f"try {new_name}({call_args})"
    else:
        call_line = f"{new_name}({call_args})"

    if has_return_type:
        new_body = f"{indent}{{\n{indent}    return {call_line}\n{indent}}}"
    else:
        new_body = f"{indent}{{\n{indent}    {call_line}\n{indent}}}"
    if DEBUG: print(f"✍️ 替换后的函数体:\n{new_body}")

    # 替换
    new_bytes = bytearray(source_bytes)
    new_bytes[body_node.start_byte:body_node.end_byte] = new_body.encode('utf-8')

    if DEBUG: print(f"✅ 已将 {signature} 改写为调用 {new_name}（{'带 return' if has_return_type else '无 return'}）")
    return bytes(new_bytes)

def rewrite_original_functions_to_call_copies(tree, source_bytes, function_map, parser):
    # 用 (class_name, signature) 作为唯一 key
    signature_map = {(r["class_name"], r["original_signature"]): r for r in function_map}
    modified_signatures = set()

    round_count = 0
    while len(modified_signatures) < len(signature_map):
        round_count += 1
        tree = parser.parse(source_bytes)
        func_nodes = recursive_find_functions(tree.root_node)

        if DEBUG: print(f"\n===== 🔄 Round {round_count}：共解析到 {len(func_nodes)} 个函数 =====")
        if DEBUG: print(f"✅ 已改写函数: {list(modified_signatures)}")
        if DEBUG: print(f"🕐 待改写函数: {[key for key in signature_map.keys() if key not in modified_signatures]}")

        modified_this_round = 0

        for func_node in func_nodes:
            info = extract_function_info(func_node, source_bytes)
            signature = info.get("signature")
            class_name = info.get("class_name", "Unknown")
            signature_key = (class_name, signature)

            if DEBUG: print(f"\n🔍 准备尝试改写函数: {signature} in class {class_name}")

            if signature_key in signature_map and signature_key not in modified_signatures:
                if DEBUG: print(f"\n🔍 尝试改写函数: {signature} in class {class_name}")
                record = signature_map[signature_key]
                source_bytes = rewrite_single_function_body(source_bytes, func_node, record)
                modified_signatures.add(signature_key)
                modified_this_round += 1

        if modified_this_round == 0:
            if DEBUG: print("⚠️ 本轮未找到可改写的函数，可能已经全部完成或有剩余未匹配函数。")
            break

    if DEBUG: print("\n🎉 所有函数改写完成。")
    return source_bytes

# =====================
# 插入If调用逻辑
# =====================

def analyze_function_returns(func_node, source_code_bytes):
    for idx, child in enumerate(func_node.children):
        if child.type == '->':
            # 有返回值
            next_node = func_node.children[idx + 1] if idx + 1 < len(func_node.children) else None
            if next_node and next_node.type == "optional_type":
                return "can_be_nil"
            return "must_return"
    return "no_return"

def is_optional_node(node):
    if node.type == "optional_type":
        return True
    for child in node.children:
        if is_optional_node(child):
            return True
    return False

def is_static_or_class_method(func_node):
    """
    检查 function_declaration 是否包含 static 或 class (包括 private static, private class 等多重修饰)
    """
    for child in func_node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                if mod_child.type == "property_modifier":
                    # 再向下看具体 static / class
                    for sub_child in mod_child.children:
                        if sub_child.type in ("static", "class"):
                            return True
                elif mod_child.type in ("static", "class"):
                    return True
        elif child.type in ("static", "class"):
            return True
        if child.type == "simple_identifier":
            # 已过参数声明，提前停止
            break
    return False

def insert_if_into_single_function_body(source_bytes, func_node, record, class_bool_map):
    new_name = record["new_name"]
    param_bool = record["bool_param"]
    class_name = record.get("class_name", "Unknown")
    copied_signature = record["copied_signature"]

    body_node = next((c for c in func_node.children if c.type == "function_body"), None)
    if not body_node:
        if DEBUG: print(f"⚠️ 未在 {new_name} 找到 function_body，跳过")
        return source_bytes

    brace_node = find_function_body_brace(func_node)
    if not brace_node:
        return source_bytes

    # 判断函数返回类型
    return_type = analyze_function_returns(func_node, source_bytes)

    # 随机选一个假方法模板
    fake_method_code = generate_method(has_return=False)
    if DEBUG: print("=== fake_method_code ===")
    if DEBUG: print(fake_method_code)

    SWIFT_LANGUAGE = Language(tsp_swift.language())
    parser = Parser(language=SWIFT_LANGUAGE)

    call_method_tree = parser.parse(fake_method_code.encode('utf-8'))
    call_method_root_node = call_method_tree.root_node
    if DEBUG: print("=== Parsed tree root node ===")
    if DEBUG: print(f"root_node type: {call_method_root_node.type}, children count: {len(call_method_root_node.children)}")

    need_call_func_name = None
    for child in call_method_root_node.children:
        if DEBUG: print(f"child type: {child.type}")
        if child.type == "function_declaration":
            need_call_func_name = extract_function_name(child, fake_method_code.encode('utf-8'))
            if DEBUG: print(f"Extracted function name: {need_call_func_name}")

    # 调用假方法
    fake_call = ""
    if need_call_func_name:
        fake_call = f"{need_call_func_name}()"
    else:
        fake_call = ""

    if DEBUG: print(f"Fake call string: {fake_call}")

    if is_static_or_class_method(func_node):
        # 类方法，不用 self 访问成员变量
        condition = f"{param_bool}"
        message = f"{param_bool} is true"
    else:
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

    # 缩进
    line_start = source_bytes.rfind(b'\n', 0, body_node.start_byte) + 1
    line = source_bytes[line_start:body_node.start_byte].decode('utf-8')
    indent_match = re.match(r'\s*', line)
    indent = indent_match.group(0) if indent_match else ""


    # 插入到 { 后面
    insert_pos = brace_node.end_byte
    new_bytes = bytearray(source_bytes)
    new_bytes[insert_pos:insert_pos] = insert_logic.encode('utf-8')

    if DEBUG: print(f"✅ 已在 {new_name} 中插入 if 逻辑: {condition}")
    return bytes(new_bytes)

def insert_if_to_copied_functions(tree, source_bytes, function_map, parser, class_bool_map):
    signature_map = {r["copied_signature"]: r for r in function_map}
    modified_signatures = set()

    round_count = 0
    while len(modified_signatures) < len(signature_map):
        round_count += 1
        tree = parser.parse(source_bytes)
        func_nodes = recursive_find_functions(tree.root_node)

        if DEBUG: print(f"\n===== 🔄 Round {round_count}：共解析到 {len(func_nodes)} 个函数 =====")
        if DEBUG: print(f"✅ 已插入 if 的函数签名: {list(modified_signatures)}")
        if DEBUG: print(f"🕐 待插入 if 的函数签名: {[sig for sig in signature_map.keys() if sig not in modified_signatures]}")

        modified_this_round = 0

        for func_node in func_nodes:
            info = extract_function_info(func_node, source_bytes)
            signature = info.get("signature")
            if DEBUG: print(f"\n🔓 准备处理方法并 if: {signature}")
            if signature in signature_map and signature not in modified_signatures:
                if DEBUG: print(f"\n🔍 尝试在复制函数中插入 if: {signature}")
                record = signature_map[signature]
                source_bytes = insert_if_into_single_function_body(source_bytes, func_node, record, class_bool_map)
                modified_signatures.add(signature)
                modified_this_round += 1

        if modified_this_round == 0:
            if DEBUG: print("⚠️ 本轮未找到可插入 if 的函数，可能已全部完成或有剩余未匹配函数。")
            break

    if DEBUG: print("\n🎉 所有复制函数插入 if 完成。")
    return source_bytes


# =====================
# 主流程
# =====================

def process_swift_file(source_path):
    source_code = open(source_path, 'rb').read()

    SWIFT_LANGUAGE = Language(tsp_swift.language())
    parser = Parser(language=SWIFT_LANGUAGE)

    # 第一步: 插入 class 成员
    tree = parser.parse(source_code)
    new_source, class_bool_map = insert_bool_properties_to_class(tree, source_code)

    # 2. 生成复制函数信息
    tree = parser.parse(new_source)
    function_map = generate_copied_functions(tree, new_source)

    # 3. 将复制函数插入到原函数后
    new_source = insert_copied_functions_after_originals(new_source, function_map)

    # 4. 改写原函数为调用复制函数
    tree = parser.parse(new_source)
    new_source = rewrite_original_functions_to_call_copies(tree, new_source, function_map, parser)

    # 5. 在复制函数内插入 if 调用
    tree = parser.parse(new_source)
    new_source = insert_if_to_copied_functions(tree, new_source, function_map, parser, class_bool_map)

    # 6. 打印结果
    print("\n===== 最终修改后的文件内容 =====\n")
    print(new_source.decode('utf-8'))

    # # 7. 想保存就解开：
    # with open(source_path, "wb") as f:
    #     f.write(new_source)
    # print(f"✅ 文件已保存：{source_path}")

# =====================
# 脚本入口
# =====================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <Swift file>")
        sys.exit(1)
    source_path = sys.argv[1]
    process_swift_file(source_path)