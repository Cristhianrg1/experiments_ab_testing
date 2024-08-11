def normal_approximation(n, p):
    """
    Verifica si la aproximación normal es válida para una proporción muestral.
    
    Parámetros:
    n (int): Tamaño de la muestra.
    p (float): Proporción muestral (éxitos / n).
    
    Retorna:
    bool: True si la aproximación normal es válida, False en caso contrario.
    """
    if n * p >= 5 and n * (1 - p) >= 5:
        return True
    else:
        return False