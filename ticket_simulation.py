from test import Digiturno
import sys, sqlite3
from PyQt5.QtWidgets import QApplication

def test_db():
    # Create test instance
    app = QApplication(sys.argv) 
    window = Digiturno()
    
    # Simulate 3 tickets
    window.handle_new_ticket("ID111", True, "C")
    window.handle_new_ticket("ID222", False, "A")
    window.handle_new_ticket("ID333", True, "H")
    window.handle_new_ticket("ID343", True, "B")
    window.handle_new_ticket("ID353", True, "F")
    window.handle_new_ticket("ID363", False, "I")
    window.handle_new_ticket("ID373", True, "A")
    window.handle_new_ticket("ID383", False, "D")
    
    # Verify database
    conn = sqlite3.connect('digiturno.db')
    cursor = conn.cursor()
    
    print("Clientes:")
    cursor.execute("SELECT * FROM clientes")
    print(cursor.fetchall())
    
    print("\nTurnos:")
    cursor.execute("SELECT servicio, numero, strftime('%Y-%m-%d', creado) FROM turnos")
    print(cursor.fetchall())
    
    conn.close()
    app.quit()