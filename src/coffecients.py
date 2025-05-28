import itertools

def evaluate_function(expr, xa, xb, xc):
    # Replace variables in string and evaluate the Boolean expression
    expr_eval = expr.replace("Xa", str(xa)).replace("Xb", str(xb)).replace("Xc", str(xc))
    return eval(expr_eval) % 2 

def compute_standard_inner_product(func_expr):
    n = 3  
    coeffs = {}

    for a_bits in itertools.product([0, 1], repeat=n):
        sum_value = 0
        for x_bits in itertools.product([0, 1], repeat=n):
            xa, xb, xc = x_bits
            f_x = evaluate_function(func_expr, xa, xb, xc)
            f_sign = (-1) ** f_x

            a_dot_x = (a_bits[0] * xa) ^ (a_bits[1] * xb) ^ (a_bits[2] * xc)
            chi_sign = (-1) ** a_dot_x

            sum_value += f_sign * chi_sign

        coeff = sum_value / (2 ** n)
        coeffs["".join(map(str, a_bits))] = coeff

    return coeffs


if __name__ == "__main__":
    func_input = input("enter the function")  
    coefficients = compute_standard_inner_product(func_input)

    print("Coefficients (standard inner product):")
    for a, c in coefficients.items():
        print(f"a = {a} → {c}")
