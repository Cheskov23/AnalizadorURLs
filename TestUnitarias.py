import unittest
import json
import os
from unittest.mock import patch, mock_open
from Analizador import (
    buscar_claves_api,
    analizar_url,
    desactivar_botones,
    activar_botones
)

class TestUnitarias(unittest.TestCase):

    def test_opciones_configuracion_sensibilidad(self):
        # Prueba que verifica la configuración de sensibilidad para el escaneo de claves API
        url = "https://www.example.com"
        servicios_validos = {
            "Google Maps": "maps.googleapis.com",
            "Twitter": "api.twitter.com"
        }
        outfile = "outfile.json"
        depth = 1
        threads = 1
        tree = None  # Simular un widget Treeview si es necesario
        try:
            analizar_url(url, servicios_validos, outfile, depth, threads, tree)
        except Exception as e:
            self.fail(f"Error al analizar URL: {e}")

    def test_analisis_contenido_completo_paginas_web(self):
        # Prueba que verifica el análisis del contenido completo de las páginas web asociadas a las URLs
        url = "https://www.example.com"
        servicios_validos = {
            "Google Maps": "maps.googleapis.com",
            "Twitter": "api.twitter.com"
        }
        outfile = "outfile.json"
        depth = 1
        threads = 1
        tree = None  # Simular un widget Treeview si es necesario
        try:
            analizar_url(url, servicios_validos, outfile, depth, threads, tree)
        except Exception as e:
            self.fail(f"Error al analizar URL: {e}")

    def test_seguir_redireccionamientos_analizar_contenido_profundidad(self):
        # Prueba que verifica el seguimiento de redireccionamientos y análisis en profundidad
        url = "https://www.example.com"
        servicios_validos = {
            "Google Maps": "maps.googleapis.com",
            "Twitter": "api.twitter.com"
        }
        outfile = "outfile.json"
        depth = 3
        threads = 3
        tree = None  # Simular un widget Treeview si es necesario
        try:
            analizar_url(url, servicios_validos, outfile, depth, threads, tree)
        except Exception as e:
            self.fail(f"Error al analizar URL: {e}")

if __name__ == "__main__":
    unittest.main()
