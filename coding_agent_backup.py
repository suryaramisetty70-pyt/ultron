# ==========================================
# CREATE PYTHON FILE
# ==========================================

def create_python_file(

    filename,

    code
):

    try:

        with open(

            filename,

            "w",

            encoding="utf-8"

        ) as f:

            f.write(code)

        return (
            f"{filename} created successfully."
        )

    except Exception as e:

        return (
            f"File creation error: {e}"
        )

# ==========================================
# GENERATE PYTHON PROGRAM
# ==========================================

def generate_python_program(topic):

    topic = topic.lower()

    # ======================================
    # HELLO PROGRAM
    # ======================================

    if "hello" in topic:

        return '''

print("Hello World")

'''

    # ======================================
    # CALCULATOR PROGRAM
    # ======================================

    if "calculator" in topic:

        return '''

a = int(input("Enter first number: "))
b = int(input("Enter second number: "))

print("Addition =", a + b)
print("Subtraction =", a - b)
print("Multiplication =", a * b)
print("Division =", a / b)

'''

    # ======================================
    # DEFAULT PROGRAM
    # ======================================

    return '''

print("Buddy AI Generated Program")

'''