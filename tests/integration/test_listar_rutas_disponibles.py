def test_listar_rutas_disponibles():
    from app.main import app
    rutas = sorted(route.path for route in app.routes)
    print("\n==== RUTAS DISPONIBLES ====\n", "\n".join(rutas))
    assert rutas, "La aplicación no tiene rutas registradas"
