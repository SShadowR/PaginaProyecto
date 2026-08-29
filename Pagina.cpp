#include <iostream>
#include <fstream>

using namespace std;

int main() {
    // Creamos el archivo index.html que será nuestra página web final
    ofstream archivo("index.html");

    if (!archivo.is_open()) {
        cout << "Error al crear el archivo HTML." << endl;
        return 1;
    }

    // Escribimos todo el contenido profesional con HTML y CSS avanzado
    archivo << "<!DOCTYPE html>\n";
    archivo << "<html lang=\"es\">\n";
    archivo << "<head>\n";
    archivo << "    <meta charset=\"UTF-8\">\n";
    archivo << "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n";
    archivo << "    <title>Portafolio Profesional | C++</title>\n";
    archivo << "    <style>\n";
    archivo << "        * { margin: 0; padding: 0; box-sizing: border-box; }\n";
    archivo << "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }\n";
    archivo << "        .container { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px; border-radius: 20px; text-align: center; max-width: 500px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }\n";
    archivo << "        h1 { color: #38bdf8; font-size: 2.2rem; margin-bottom: 15px; }\n";
    archivo << "        p { color: #94a3b8; font-size: 1.1rem; line-height: 1.6; margin-bottom: 25px; }\n";
    archivo << "        .btn { display: inline-block; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: white; padding: 12px 30px; border-radius: 30px; text-decoration: none; font-weight: bold; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4); }\n";
    archivo << "        .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(56, 189, 248, 0.6); }\n";
    archivo << "    </style>\n";
    archivo << "</head>\n";
    archivo << "<body>\n";
    archivo << "    <div class=\"container\">\n";
    archivo << "        <h1>¡Hola desde C++!</h1>\n";
    archivo << "        <p>Esta página web profesional ha sido generada compilando y ejecutando código nativo en C++.</p>\n";
    archivo << "        <a href=\"#\" class=\"btn\">Conoce Más</a>\n";
    archivo << "    </div>\n";
    archivo << "</body>\n";
    archivo << "</html>\n";

    archivo.close();
    cout << "¡Página web profesional generada con exito desde C++!" << endl;

    return 0;
}