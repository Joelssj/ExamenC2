from flask import Flask, request, render_template_string
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

reservadas = {
    'int': 'INT',
    'DO': 'DO',
    'ENDDO': 'ENDDO',
    'WHILE': 'WHILE',
    'ENDWHILE': 'ENDWHILE'
}

tokens = (
    'ID', 'ASSIGN', 'NUMBER', 'SEMICOLON', 'PLUS', 'TIMES', 'LPAREN', 'RPAREN', 'EQUALS'
) + tuple(reservadas.values())

t_ASSIGN = r'='
t_SEMICOLON = r';'
t_PLUS = r'\+'
t_TIMES = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EQUALS = r'=='

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reservadas.get(t.value, 'ID')
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

analizadorLexico = lex.lex()

variables = set()
errores_sintacticos = []
errores_semanticos = []

def p_programa(p):
    '''programa : declaraciones DO bloque ENDDO WHILE LPAREN condicion RPAREN ENDWHILE'''
    p[0] = ('programa', p[1], p[3], p[7])

def p_declaraciones(p):
    '''declaraciones : declaraciones declaracion
                     | declaracion'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    '''declaracion : INT ID ASSIGN NUMBER SEMICOLON'''
    if p[2] in variables:
        errores_semanticos.append(f"Error: Variable '{p[2]}' redeclarada.")
    else:
        variables.add(p[2])
    p[0] = ('declaracion', p[2], p[4])

def p_bloque(p):
    '''bloque : bloque sentencia
              | sentencia'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_sentencia(p):
    '''sentencia : ID ASSIGN expresion SEMICOLON'''
    if p[1] not in variables:
        errores_semanticos.append(f"Error: Variable '{p[1]}' no declarada.")
    p[0] = ('sentencia', p[1], p[3])

def p_expresion(p):
    '''expresion : termino
                 | termino PLUS termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('+', p[1], p[3])

def p_termino(p):
    '''termino : factor
               | factor TIMES factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('*', p[1], p[3])

def p_factor(p):
    '''factor : NUMBER
              | ID'''
    if isinstance(p[1], str) and p[1] not in variables:
        errores_semanticos.append(f"Error: Variable '{p[1]}' no declarada.")
    p[0] = p[1]

def p_condicion(p):
    '''condicion : tipo ID EQUALS NUMBER
                 | ID EQUALS NUMBER'''
    if len(p) == 4:
        if p[1] not in variables:
            errores_semanticos.append(f"Error: Variable '{p[1]}' no declarada en la condición.")
    else:
        if p[2] in variables:
            errores_semanticos.append(f"Error: Variable '{p[2]}' redeclarada en la condición.")
        else:
            variables.add(p[2])
    p[0] = ('condicion', p[1], p[3], p[4])

def p_tipo(p):
    '''tipo : INT'''
    p[0] = p[1]

def p_error(p):
    if p:
        errores_sintacticos.append(f"Error de sintaxis en '{p.value}'")
    else:
        errores_sintacticos.append("Error de sintaxis en EOF")

analizadorSintactico = yacc.yacc()

@app.route('/', methods=['GET', 'POST'])
def index():
    global errores_sintacticos
    global errores_semanticos
    global variables
    errores_sintacticos = []
    errores_semanticos = []
    variables = set()
    resultado_lexico = ""
    conteoTokens = {
        'ID': 0, 'PR': 0, 'NUMEROS': 0, 'SIMBOLOS': 0, 'ERRORES': 0, 'TOTAL': 0
    }
    if request.method == 'POST':
        codigo = request.form['codigo']
        analizadorLexico.input(codigo)
        listaTokens = []
        while True:
            tok = analizadorLexico.token()
            if not tok:
                break
            listaTokens.append(str(tok))
            if tok.type in conteoTokens:
                conteoTokens[tok.type] += 1
            elif tok.type in reservadas.values():
                conteoTokens['PR'] += 1
            else:
                conteoTokens['SIMBOLOS'] += 1

        try:
            analizadorSintactico.parse(codigo)
            resultado_lexico = "Análisis léxico completado:\n" + "\n".join(listaTokens)
        except SyntaxError as e:
            errores_sintacticos.append(str(e))
            conteoTokens['ERRORES'] += 1
        except Exception as e:
            errores_sintacticos.append("Ocurrió un error inesperado: " + str(e))
            conteoTokens['ERRORES'] += 1

        conteoTokens['TOTAL'] = sum(conteoTokens.values())

    return render_template_string('''
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
      font-family: 'Roboto', sans-serif;
      background-color: #f5f5f5;
      margin: 0;
      padding: 20px;
      color: #333;
    }
    h1, h2 {
      text-align: center;
      color: #007BFF;
      margin-bottom: 20px;
    }
    .container {
      display: flex;
      flex-wrap: wrap;
      max-width: 1200px;
      margin: 0 auto;
    }
    .left, .right, .bottom {
      padding: 20px;
      background-color: #fff;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      margin: 10px;
    }
    .left {
      flex: 1;
      min-width: 300px;
    }
    .right {
      flex: 1;
      min-width: 300px;
    }
    .bottom {
      flex-basis: 100%;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    textarea {
      width: 100%;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-family: 'Roboto', sans-serif;
      font-size: 16px;
    }
    input[type="submit"] {
      background-color: #007BFF;
      color: white;
      padding: 14px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s ease;
      font-size: 16px;
    }
    input[type="submit"]:hover {
      background-color: #0056b3;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    table, th, td {
      border: 1px solid #ddd;
    }
    th, td {
      padding: 12px;
      text-align: left;
    }
    th {
      background-color: #007BFF;
      color: black;
    }
    tr:nth-child(even) {
      background-color: #f2f2f2;
    }
    tr:hover {
      background-color: #ddd;
    }
    .syntax-semantics {
      background-color: #1E3A5F;
      color: white;
      border-radius: 8px;
      padding: 20px;
    }
    .syntax-semantics th, .syntax-semantics td {
      color: black;
    }
  </style>
  <title>Analizador</title>
</head>
<body>
  <div class="container">
    <div class="left">
      <h2>Ingresar Código</h2>
      <form method="post">
        <textarea name="codigo" rows="10" cols="50">{{ request.form['codigo'] }}</textarea><br>
        <input type="submit" value="Analizar">
      </form>
      <div class="bottom syntax-semantics">
        <h2>Analizador Sintáctico y Semántico</h2>
        <table>
          <tr>
            <th>Sintáctico</th><th>Semántico</th>
          </tr>
          <tr>
            <td>{{ syntactic }}</td><td>{{ semantic }}</td>
          </tr>
        </table>
      </div>
    </div>
    <div class="right">
      <h2>Analizador Léxico</h2>
      <table>
        <tr>
          <th>Tokens</th><th>PR</th><th>ID</th><th>Números</th><th>Símbolos</th><th>Error</th>
        </tr>
        <tr>
          <td>Total</td><td>{{ conteoTokens['PR'] }}</td><td>{{ conteoTokens['ID'] }}</td><td>{{ conteoTokens['NUMEROS'] }}</td><td>{{ conteoTokens['SIMBOLOS'] }}</td><td>{{ conteoTokens['ERRORES'] }}</td>
        </tr>
      </table>
    </div>
  </div>
</body>
</html>
    ''', resultado=resultado_lexico, conteoTokens=conteoTokens, syntactic="Sintaxis correcta" if not errores_sintacticos else " ".join(errores_sintacticos), semantic="Uso correcto de las variables" if not errores_semanticos else " ".join(errores_semanticos))

if __name__ == '__main__':
    app.run(debug=True)

