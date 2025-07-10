import sys
from tree_sitter import Language, Parser
import tree_sitter_swift as tsp_swift

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <Swift file>")
    sys.exit(1)

source_path = sys.argv[1]
source_code = open(source_path, 'rb').read()

SWIFT_LANGUAGE = Language(tsp_swift.language())
parser = Parser(language=SWIFT_LANGUAGE)
tree = parser.parse(source_code)


def print_ast_tree(node, source_code_bytes, indent=0):
    snippet = source_code_bytes[node.start_byte:node.end_byte].decode('utf-8').replace('\n', '\\n')
    print('  ' * indent + f"-> {node.type} [{node.start_point}-{node.end_point}] : '{snippet[:40]}...'")
    for child in node.children:
        print_ast_tree(child, source_code_bytes, indent + 1)

print("\n=== Full AST ===")
print_ast_tree(tree.root_node, source_code)


# def find_nodes(node, type_name, results):
#     if node.type == type_name:
#         results.append(node)
#     for child in node.children:
#         find_nodes(child, type_name, results)

# def find_functions_within(node):
#     functions = []
#     find_nodes(node, 'function_declaration', functions)
#     return functions

# def find_variables_within(node):
#     variables = []
#     find_nodes(node, 'property_declaration', variables)
#     return variables

# def find_classes(node, results):
#     if node.type == 'class_declaration':
#         results.append(node)
#     for child in node.children:
#         find_classes(child, results)

# # ===========================
# # 打印 class 及其 members 和 functions
# # ===========================

# classes = []
# find_classes(tree.root_node, classes)

# for idx, cls in enumerate(classes):
#     start_line, start_col = cls.start_point
#     end_line, end_col = cls.end_point
#     cls_text = source_code[cls.start_byte:cls.end_byte].decode('utf-8')

#     print(f"\n===== Class #{idx+1} =====")
#     print(f"start: line {start_line+1}, column {start_col+1}")
#     print(f"end:   line {end_line+1}, column {end_col+1}")
#     print("code:")
#     print(cls_text)

#     # 输出成员变量
#     variables = find_variables_within(cls)
#     if variables:
#         for j, v in enumerate(variables):
#             v_start_line, v_start_col = v.start_point
#             v_end_line, v_end_col = v.end_point
#             var_text = source_code[v.start_byte:v.end_byte].decode('utf-8')
#             print(f"\n  ↳ Variable #{j+1}")
#             print(f"    start: line {v_start_line+1}, column {v_start_col+1}")
#             print(f"    end:   line {v_end_line+1}, column {v_end_col+1}")
#             for line in var_text.splitlines():
#                 print("    " + line)
#     else:
#         print("  ↳ (No variables found)")

#     # 输出函数
#     functions = find_functions_within(cls)
#     if functions:
#         for k, f in enumerate(functions):
#             f_start_line, f_start_col = f.start_point
#             f_end_line, f_end_col = f.end_point
#             func_text = source_code[f.start_byte:f.end_byte].decode('utf-8')
#             print(f"\n  ↳ Function #{k+1}")
#             print(f"    start: line {f_start_line+1}, column {f_start_col+1}")
#             print(f"    end:   line {f_end_line+1}, column {f_end_col+1}")
#             for line in func_text.splitlines():
#                 print("    " + line)
#     else:
#         print("  ↳ (No functions found)")

# print("\n✅ Done.")