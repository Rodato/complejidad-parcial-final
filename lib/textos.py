"""Textos del parcial: intro de cada parte y enunciados de los 11 puntos.

Diseño adaptado al hallazgo de 'bazar fragmentado' de la red real de la
Notaría 2 (1938–1944): sin brokers, mercado desconectado, pero con fuerte
concentración en la compra (cola larga). Cada punto pide ANCLAJE EMPÍRICO
en los datos mostrados, no generalidades.
"""

TITULO = "Parcial Final · La red de propiedad de la Notaría 2 de Cali (1938–1944)"

# Explicación del CV, reutilizada en tooltips y textos.
CV_AYUDA = ("CV = coeficiente de variación = desviación estándar ÷ media del "
            "nº de compras. Mide la desigualdad (sin unidades): cerca de 0 = "
            "casi todos compran parecido (campana); mayor que 1 = unos pocos "
            "concentran las compras (cola larga).")

CV_EXPLICACION = r"""
**¿Qué es el CV?** El **coeficiente de variación** es la desviación estándar
dividida por la media del nº de compras. Mide qué tan **desigual** es la
acumulación de tierra, sin importar la escala:
**CV cercano a 0** → casi todos compran parecido (**campana**, azar);
**CV mayor que 1** → unos pocos concentran muchas compras y la mayoría casi
ninguna (**cola larga**, concentración).
"""

INTRO = r"""
### ¿Quién construyó Cali?

Tienen enfrente la **red real** de compraventas protocolizadas en la **Notaría 2
de Cali entre 1938 y 1944** (708 transacciones, ~1.250 actores). La red es
**dirigida**: cada flecha va del **vendedor → comprador**, porque la tierra
fluye hacia quien compra. Por eso la métrica central es el
**grado de entrada = número de compras = acumulación de tierra**.

El parcial tiene **4 partes**. Algunas cifras ya están calculadas (las leen e
interpretan); otras las obtienen ustedes moviendo los controles. **Toda
respuesta debe apoyarse en lo que muestran los datos**, no en ideas generales.

Trabajen en **parejas (máx. 2)**. Registren sus nombres a la izquierda y
guarden cada respuesta con su botón. Pueden volver y editar hasta enviar.
"""

# Cada parte: (clave, título, intro markdown)
PARTES = {
    "I": ("Parte I · Topología de la red", r"""
Miren la forma global de la red antes de entrar en los actores.
"""),
    "II": ("Parte II · Los actores clave", r"""
¿Quién acumula, quién liquida, quién intermedia? Usen los rankings.
"""),
    "III": ("Parte III · Régimen y emergencia", r"""
¿Se **concentra** la propiedad con el tiempo? ¿Hay vinculación preferencial?
"""),
    "IV": ("Parte IV · Interpretación histórica", r"""
Junten todo: ¿qué dice esta estructura sobre cómo emergió el espacio urbano
de Cali, y qué **no** alcanza a mostrar esta red?
"""),
}

# Cada punto: clave -> (parte, título, enunciado markdown, alto_del_textarea)
PUNTOS = {
    "p1": ("I", "1. ¿Campana o cola larga?", r"""
Observen la **distribución del grado de entrada** (compras por actor) y el
**CV**. ¿La distribución se parece más a una **campana** (azar) o a una
**cola larga** (unos pocos concentran)? ¿Cuál es el **proceso** que llevó a
esa distribución? Usen la **forma** del histograma y el valor del **CV** para
justificar su respuesta.
""", 120),

    "p2": ("I", "2. ¿Por qué está tan desconectada?", r"""
La red tiene cientos de **componentes** y un **componente gigante** que apenas
cubre una fracción de los actores; además, la mayoría aparece con **sólo una
transacción**. ¿Por qué el mercado de tierra está tan **desconectado**? ¿Qué
dice esto sobre **cómo se transaba** la propiedad en Cali en esos años?
""", 120),

    "p3": ("I", "3. Casi sin triángulos", r"""
El **clustering global** es prácticamente **cero**. Es decir, casi no hay
"triángulos" (si A le vende a B y a C, B y C casi nunca cierran un trato entre
sí). ¿Qué significa que **no se formen círculos cerrados** de tratos?
""", 100),

    "p4": ("II", "4. Los mayores acumuladores de tierra", r"""
Según el **grado de entrada (compras)**, nombren los **3 mayores acumuladores
de tierra** y sus cifras. ¿Son personas, familias, empresas o instituciones?
""", 100),

    "p5": ("II", "5. ¿Dónde están los intermediarios?", r"""
La **betweenness** (centralidad por intermediación) es **≈ 0 para casi
todos**: prácticamente **no hay brokers**. (a) ¿Por qué? Relacionen este
hallazgo con la **fragmentación** de la Parte I. (b) La excepción está en
**quiénes compran Y venden mucho**: identifiquen a esos agentes, con sus
cifras, y expliquen su papel.
""", 120),

    "p6": ("II", "6. ¿Acumular tierra, área o dinero?", r"""
Cambien la **métrica del ranking** entre **nº de compras**, **área (m²)** y
**valor ($)**. ¿El mayor acumulador es **el mismo** en las tres medidas?
¿Qué revela la diferencia (p. ej. quien compra muchos lotes pequeños vs.
quien compra poca área pero muy cara)?
""", 120),

    "p7": ("II", "7. El papel del Municipio de Cali", r"""
El **Municipio de Cali** es el nodo más activo: **vende** muchísimo y también
**compra**. Miren sus cifras. ¿Qué papel jugó la **ciudad** en la formación
del suelo urbano? ¿Por qué una entidad pública encabeza un mercado de tierras?
""", 120),

    "p8": ("III", "8. ¿Se concentra la propiedad con el tiempo?", r"""
Con el **control de años (1938 → 1944)** observen el **CV del grado de
entrada** y el volumen de transacciones. ¿El CV **sube** (más concentración)?
**Salvedad obligatoria**: 1943 tiene muchísimas más transacciones que los
otros años. ¿Cómo afecta eso la comparación? ¿Pueden afirmar una tendencia?
""", 130),

    "p9": ("III", "9. ¿Vinculación preferencial?", r"""
¿Ven indicios de **vinculación preferencial** ("prefiero vender a quien ya ha
comprado antes")? Den un **ejemplo concreto** de la red (p. ej. un actor que
compra repetidamente). **Cuidado**: la cola larga es una **intuición visual**,
no una prueba estadística de ley de potencia. Redacten con esa cautela.
""", 120),

    "p10": ("IV", "10. ¿Cómo emergió el espacio urbano de Cali?", r"""
En **2–3 párrafos**, integren lo anterior: ¿qué dice esta estructura de red
sobre **cómo emergió el espacio urbano de Cali** entre 1938 y 1944?
¿**Quiénes** fueron los ganadores de la acumulación de tierra? Anclen su
argumento en actores y cifras concretas.
""", 200),

    "p11": ("IV", "11. ¿Qué NO captura esta red?", r"""
Esta red es solo lo **protocolizado en la Notaría 2** entre 1938 y 1944 —una
sola notaría, unos pocos años—. ¿Qué **queda por fuera** de esta foto de la
propiedad en Cali? ¿Qué **otra fuente o método** (de los vistos en el curso)
agregarían para entender mejor cómo se concentró la tierra?
""", 160),
}
