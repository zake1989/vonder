from tree_sitter import Language, Parser
import tree_sitter_swift as tsp_swift  # 注意包名

# tsp_swift.language() 返回 swift 对应的 Language 对象
SWIFT_LANGUAGE = Language(tsp_swift.language())
# 或直接是： SWIFT_LANGUAGE = tsp_swift.language()

parser = Parser(language=SWIFT_LANGUAGE)

def print_node(node, source_code, indent=0):
    print('  ' * indent + f"{node.type}: '{node.text.decode()}'")
    for child in node.children:
        print_node(child, source_code, indent + 1)

source_code = b"class A { var need: Bool = true  func f() {} }"
tree = parser.parse(source_code)
print_node(tree.root_node, source_code)