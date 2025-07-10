from method_generator import generate_method

if __name__ == "__main__":
    # 生成一个有返回值的方法
    code_with_return = generate_method(has_return=True)
    print("=== 有返回值方法 ===")
    print(code_with_return)
    
    print()
    
    # 生成一个无返回值的方法
    code_void = generate_method(has_return=False)
    print("=== 无返回值方法 ===")
    print(code_void)