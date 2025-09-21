import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGridLayout, QHBoxLayout, QVBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt



#  Utilidad: conversión segura de texto a float 


def to_float(texto: str) -> float:
    """Convierte texto a float de forma segura.
    - Acepta comas o puntos decimales.
    - Retorna 0.0 si está vacío.
    - Retorna NaN si el valor no es convertible.
    """
    if texto is None:
        return 0.0
    texto = texto.strip().replace(",", ".")
    if texto == "":
        return 0.0
    try:
        return float(texto)
    except ValueError:
        return float("nan")  # Indicador de valor inválido



#  Ventana principal de la aplicación

class AppSueldos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cálculo de Sueldos de Vendedores - PyQt5")
        self.setMinimumWidth(880)
        self.init_ui()  # Construye la interfaz

    
    #  Construcción de la interfaz
    
    def init_ui(self):
        #  ENTRADAS
        self.le_nombre = QLineEdit()
        self.le_nombre.setPlaceholderText("Nombre y apellido del vendedor")

        self.le_base = QLineEdit()
        self.le_base.setPlaceholderText("0.00")
        self.le_base.setMaximumWidth(140)

        self.le_ventas = QLineEdit()
        self.le_ventas.setPlaceholderText("0.00")
        self.le_ventas.setMaximumWidth(140)

        # % de comisión: QComboBox editable con opciones frecuentes
        self.cb_porcentaje = QComboBox()
        self.cb_porcentaje.setEditable(True)
        self.cb_porcentaje.addItems(["2.5", "5", "7.5", "10"])
        self.cb_porcentaje.setCurrentText("5")
        self.cb_porcentaje.setToolTip("Porcentaje de comisión sobre ventas (ej. 5 = 5%)")
        self.cb_porcentaje.setMaximumWidth(120)

        # Tipo de vendedor (ejemplo de regla de negocio: Senior suma 2% a la comisión)
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Junior", "Senior"])
        self.cb_tipo.setMaximumWidth(120)

        # Bono por meta alcanzada (controlable con un checkbox)
        self.chk_bono = QCheckBox("Aplicar bono por meta")
        self.le_meta = QLineEdit()
        self.le_meta.setPlaceholderText("Meta ventas (ej. 3000)")
        self.le_meta.setMaximumWidth(140)

        self.le_bono = QLineEdit()
        self.le_bono.setPlaceholderText("Monto bono (ej. 100)")
        self.le_bono.setMaximumWidth(140)

        #  SALIDAS (resultados) 
        self.lbl_comision = QLabel("Comisión: $0.00")
        self.lbl_bono = QLabel("Bono: $0.00")
        self.lbl_total = QLabel("<b>Sueldo Total: $0.00</b>")

        #  BOTONES 
        self.btn_calcular = QPushButton("Calcular")
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_agregar = QPushButton("Agregar a tabla")
        self.btn_exportar = QPushButton("Exportar CSV")

        # Conectar señales con slots (funciones)
        self.btn_calcular.clicked.connect(self.calcular)
        self.btn_limpiar.clicked.connect(self.limpiar)
        self.btn_agregar.clicked.connect(self.agregar_a_tabla)
        self.btn_exportar.clicked.connect(self.exportar_csv)

        #  TABLA para registrar cálculos 
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            "Vendedor", "Tipo", "Base ($)", "Ventas ($)", "% Com.",
            "Bono ($)", "Total ($)"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)

        #  Layouts / Organización visual 
        gb_inputs = QGroupBox("Datos de entrada")
        grid = QGridLayout()
        fila = 0
        grid.addWidget(QLabel("Vendedor:"), fila, 0)
        grid.addWidget(self.le_nombre, fila, 1, 1, 3)

        fila += 1
        grid.addWidget(QLabel("Sueldo base ($):"), fila, 0)
        grid.addWidget(self.le_base, fila, 1)
        grid.addWidget(QLabel("Ventas del mes ($):"), fila, 2)
        grid.addWidget(self.le_ventas, fila, 3)

        fila += 1
        grid.addWidget(QLabel("% Comisión:"), fila, 0)
        grid.addWidget(self.cb_porcentaje, fila, 1)
        grid.addWidget(QLabel("Tipo vendedor:"), fila, 2)
        grid.addWidget(self.cb_tipo, fila, 3)

        fila += 1
        grid.addWidget(self.chk_bono, fila, 0, 1, 2)
        grid.addWidget(QLabel("Meta ($):"), fila, 2)
        grid.addWidget(self.le_meta, fila, 3)

        fila += 1
        grid.addWidget(QLabel("Bono ($):"), fila, 2)
        grid.addWidget(self.le_bono, fila, 3)

        gb_inputs.setLayout(grid)

        gb_resultados = QGroupBox("Resultados")
        box_res = QVBoxLayout()
        box_res.addWidget(self.lbl_comision)
        box_res.addWidget(self.lbl_bono)
        box_res.addWidget(self.lbl_total)
        gb_resultados.setLayout(box_res)

        box_botones = QHBoxLayout()
        box_botones.addWidget(self.btn_calcular)
        box_botones.addWidget(self.btn_limpiar)
        box_botones.addStretch(1)
        box_botones.addWidget(self.btn_agregar)
        box_botones.addWidget(self.btn_exportar)

        root = QVBoxLayout()
        root.addWidget(gb_inputs)
        root.addWidget(gb_resultados)
        root.addLayout(box_botones)
        root.addWidget(self.tabla)

        self.setLayout(root)

    
    #  Lógica de validación y cálculo
    
    def validar_inputs(self):
        """Valida y transforma las entradas; devuelve un dict o None si hay error."""
        nombre = self.le_nombre.text().strip()
        base = to_float(self.le_base.text())
        ventas = to_float(self.le_ventas.text())
        pct = to_float(self.cb_porcentaje.currentText())
        aplicar_bono = self.chk_bono.isChecked()
        meta = to_float(self.le_meta.text())
        bono = to_float(self.le_bono.text())

        # Helper para detectar NaN sin importar plataforma
        def es_nan(x):
            return x != x

        # Validación de nombre
        if nombre == "":
            self.alerta("Por favor, ingresa el nombre del vendedor.")
            return None

        # Validar que base, ventas y porcentaje sean números válidos
        if any(es_nan(x) for x in [base, ventas, pct]):
            self.alerta("Revisa Base, Ventas y % Comisión (solo números).")
            return None

        # No permitir números negativos
        if base < 0 or ventas < 0 or pct < 0:
            self.alerta("Valores inválidos: no pueden ser negativos.")
            return None

        # Validar bono/meta si el checkbox está activo
        if aplicar_bono:
            if any(es_nan(x) for x in [meta, bono]):
                self.alerta("Meta y Bono deben ser números válidos.")
                return None
            if meta < 0 or bono < 0:
                self.alerta("Meta y Bono deben ser ≥ 0.")
                return None

        return {
            "nombre": nombre,
            "base": base,
            "ventas": ventas,
            "pct": pct,
            "tipo": self.cb_tipo.currentText(),
            "aplicar_bono": aplicar_bono,
            "meta": meta if aplicar_bono else 0.0,
            "bono": bono if aplicar_bono else 0.0,
        }

    def calcular(self):
        """Calcula comisión, bono (si aplica) y sueldo total; muestra resultados."""
        datos = self.validar_inputs()
        if not datos:
            return

        # Comisión base: ventas * (pct/100)
        comision = datos["ventas"] * (datos["pct"] / 100.0)

        # Regla ejemplo: si es Senior, recibe 2% extra sobre la comisión calculada
        if datos["tipo"] == "Senior":
            comision *= 1.02

        # Bono por meta: aplica solo si el checkbox está activo y se alcanza la meta
        bono_aplicado = 0.0
        if datos["aplicar_bono"] and datos["ventas"] >= datos["meta"]:
            bono_aplicado = datos["bono"]

        total = datos["base"] + comision + bono_aplicado

        # Mostrar resultados en las etiquetas
        self.lbl_comision.setText(f"Comisión: ${comision:,.2f}")
        self.lbl_bono.setText(f"Bono: ${bono_aplicado:,.2f}")
        self.lbl_total.setText(f"<b>Sueldo Total: ${total:,.2f}</b>")

        # Guardar el último cálculo para poder agregarlo a la tabla sin recalcular
        self._ultimo_resultado = {
            "nombre": datos["nombre"],
            "tipo": datos["tipo"],
            "base": datos["base"],
            "ventas": datos["ventas"],
            "pct": datos["pct"],
            "bono": bono_aplicado,
            "total": total,
        }

    def agregar_a_tabla(self):
        """Inserta el último resultado calculado como una fila en la tabla."""
        if not hasattr(self, "_ultimo_resultado"):
            self.alerta("Primero realiza un cálculo.")
            return
        r = self._ultimo_resultado
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, 0, QTableWidgetItem(r["nombre"]))
        self.tabla.setItem(fila, 1, QTableWidgetItem(r["tipo"]))
        self.tabla.setItem(fila, 2, QTableWidgetItem(f"{r['base']:.2f}"))
        self.tabla.setItem(fila, 3, QTableWidgetItem(f"{r['ventas']:.2f}"))
        self.tabla.setItem(fila, 4, QTableWidgetItem(f"{r['pct']:.2f}"))
        self.tabla.setItem(fila, 5, QTableWidgetItem(f"{r['bono']:.2f}"))
        self.tabla.setItem(fila, 6, QTableWidgetItem(f"{r['total']:.2f}"))

    def exportar_csv(self):
        """Guarda el contenido de la tabla en un archivo .csv."""
        if self.tabla.rowCount() == 0:
            self.alerta("No hay datos en la tabla para exportar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "sueldos.csv", "CSV (*.csv)")
        if not ruta:
            return  # Usuario canceló
        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Encabezados
                headers = [self.tabla.horizontalHeaderItem(i).text() for i in range(self.tabla.columnCount())]
                writer.writerow(headers)
                # Filas de datos
                for fila in range(self.tabla.rowCount()):
                    fila_datos = []
                    for col in range(self.tabla.columnCount()):
                        item = self.tabla.item(fila, col)
                        fila_datos.append(item.text() if item else "")
                    writer.writerow(fila_datos)
            QMessageBox.information(self, "Éxito", f"Archivo guardado en:\n{ruta}")
        except Exception as e:
            self.alerta(f"Ocurrió un error al guardar:\n{e}")

    def limpiar(self):
        """Restablece todos los campos y resultados a su estado inicial."""
        self.le_nombre.clear()
        self.le_base.clear()
        self.le_ventas.clear()
        self.cb_porcentaje.setCurrentText("5")
        self.cb_tipo.setCurrentIndex(0)
        self.chk_bono.setChecked(False)
        self.le_meta.clear()
        self.le_bono.clear()
        self.lbl_comision.setText("Comisión: $0.00")
        self.lbl_bono.setText("Bono: $0.00")
        self.lbl_total.setText("<b>Sueldo Total: $0.00</b>")
        if hasattr(self, "_ultimo_resultado"):
            delattr(self, "_ultimo_resultado")

    
    #  Utilidades de la clase
    
    def alerta(self, msg: str):
        """Muestra un cuadro de advertencia estandarizado."""
        QMessageBox.warning(self, "Validación", msg)



#  Punto de entrada de la aplicación

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AppSueldos()
    win.show()
    sys.exit(app.exec_())
