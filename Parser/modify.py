import sys
from tree_sitter import Language, Parser
import tree_sitter_swift as tsp_swift

import json
import random
import string


# =====================
# 读取 Bool 名称列表
# =====================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

variable_names_pool = config.get("bool_names", [])

def random_suffix():
    length = random.randint(3, 6)
    letters_and_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choices(letters_and_digits, k=length))

def generate_variable_name():
    base = random.choice(variable_names_pool)
    suffix = random_suffix()
    # 第一个字母大写，其余小写（数字保持）
    return base + suffix.capitalize()

def generate_bool_declarations(count=1):
    """生成 count 个 Bool 变量声明字符串列表，变量名用已有的 generate_variable_name()"""
    declarations = []
    for _ in range(count):
        var_name = generate_variable_name()  # 复用已有的函数
        var_value = random.choice(["true", "false"])
        declarations.append(f"    var {var_name}: Bool = {var_value}")
    return declarations

# =====================
# 辅助调试函数
# =====================

def print_function_tree(node, source_code_bytes, indent=0):
    print('  ' * indent + f"{node.type}: '{source_code_bytes[node.start_byte:node.end_byte].decode('utf-8')}'")
    for child in node.children:
        print_function_tree(child, source_code_bytes, indent + 1)

# =====================
# 递归查找参数括号
# =====================

def find_and_rebuild_parameters(node, source_code_bytes):
    start_paren = None
    end_paren = None
    for child in node.children:
        if child.type == '(' and start_paren is None:
            start_paren = child
        if child.type == ')':
            end_paren = child
    if start_paren and end_paren:
        return start_paren, end_paren
    # 没找到就递归继续找
    for child in node.children:
        sub_start, sub_end = find_and_rebuild_parameters(child, source_code_bytes)
        if sub_start and sub_end:
            return sub_start, sub_end
    return None, None

# =====================
# 修改函数参数列表
# =====================

def modify_function(func_node, source_code_bytes):
    print("\n=== Function Declaration ===")
    # print_function_tree(func_node, source_code_bytes)

    start_paren, end_paren = find_and_rebuild_parameters(func_node, source_code_bytes)
    if not start_paren or not end_paren:
        print(" -> ⚠️ 未找到 '(' ')' 参数范围，跳过")
        return source_code_bytes[func_node.start_byte:func_node.end_byte]

    old_params = source_code_bytes[start_paren.start_byte:end_paren.end_byte].decode('utf-8')
    print(f" - 原参数: {old_params}")

    new_var_name = generate_variable_name()

    if old_params == '()':
        new_params = f'({new_var_name}: Bool = false)'
    else:
        new_params = old_params[:-1] + f', {new_var_name}: Bool = false)'

    print(f" - 新参数: {new_params}")

    new_func_code = (
        source_code_bytes[func_node.start_byte:start_paren.start_byte].decode('utf-8') +
        new_params +
        source_code_bytes[end_paren.end_byte:func_node.end_byte].decode('utf-8')
    )

    return new_func_code.encode('utf-8')

# =====================
# 找所有 function_declaration 查找 class
# =====================

def find_functions(node, results):
    if node.type == 'function_declaration':
        results.append(node)
    for child in node.children:
        find_functions(child, results)

def find_class_nodes(node, results=None):
    if results is None:
        results = []
    if node.type == "class_declaration":
        results.append(node)
    for child in node.children:
        find_class_nodes(child, results)
    return results

# =====================
# 找所有 class 然后插入 Bool
# =====================

def find_class_body_brace_node(class_node):
    # class_node 的 children 有一个是 class_body
    for child in class_node.children:
        if child.type == "class_body":
            for grandchild in child.children:
                if grandchild.type == "{":
                    return grandchild
    return None

def insert_bool_properties_to_class(tree, source_code_bytes):
    classes = find_class_nodes(tree.root_node)
    print(f"=== 找到 {len(classes)} 个 class，准备插入 Bool 成员 ===")
    classes.sort(key=lambda n: n.start_byte, reverse=True)

    output_parts = []
    last_index = len(source_code_bytes)

    for idx, cls in enumerate(classes, start=1):
        brace_node = find_class_body_brace_node(cls)
        if not brace_node:
            print(f" - ⚠️ class #{idx} 未找到 '{{'，跳过")
            continue
        insert_pos = brace_node.end_byte
        count = random.randint(1, 3)
        declarations = generate_bool_declarations(count)
        insert_text = "\n" + "\n".join(declarations)
        print(f" - ✅ 在 class #{idx} 插入 {count} 个 Bool 成员")
        output_parts.append(source_code_bytes[insert_pos:last_index])
        output_parts.append(insert_text.encode('utf-8'))
        last_index = insert_pos

    output_parts.append(source_code_bytes[:last_index])
    new_source = b"".join(reversed(output_parts))
    print("=== 类成员插入完成 ===")
    return new_source

# =====================
# 读取 Swift 代码
# =====================

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <Swift file>")
    sys.exit(1)

source_path = sys.argv[1]
source_code = open(source_path, 'rb').read()

SWIFT_LANGUAGE = Language(tsp_swift.language())
parser = Parser(language=SWIFT_LANGUAGE)
tree = parser.parse(source_code)

# =====================
# 主逻辑
# =====================

# 先插入类的 Bool 成员
new_source_code = insert_bool_properties_to_class(tree, source_code)

# 需要重新 parse，因为已经修改了
tree = parser.parse(new_source_code)

# 再对函数插入参数
functions = []
find_functions(tree.root_node, functions)
functions.sort(key=lambda n: n.start_byte)

output_parts = []
last_index = 0
for f in functions:
    output_parts.append(new_source_code[last_index:f.start_byte])
    new_func_bytes = modify_function(f, new_source_code)
    output_parts.append(new_func_bytes)
    last_index = f.end_byte

output_parts.append(new_source_code[last_index:])
final_code = b''.join(output_parts).decode('utf-8')

print("\n===== 最终修改后的文件内容 =====")
print(final_code)