"""
Utilidades para DevDocs MCP
Conversión HTML a Markdown y otras funciones auxiliares
"""
import re


def html_to_markdown(html_content: str) -> str:
    """
    Convierte HTML a Markdown de forma simple pero efectiva.
    Optimizado para el formato de documentación de DevDocs.
    """
    if not html_content:
        return ""
    
    # Remover scripts y estilos
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    
    # Convertir headings
    html_content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'\n##### \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'\n###### \1\n', html_content, flags=re.DOTALL)
    
    # Convertir bloques de código (pre antes que code para evitar conflictos)
    html_content = re.sub(
        r'<pre[^>]*><code[^>]*class="([^"]*)"[^>]*>(.*?)</code></pre>',
        lambda m: f'\n```{extract_language(m.group(1))}\n{m.group(2)}\n```\n',
        html_content,
        flags=re.DOTALL
    )
    html_content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', html_content, flags=re.DOTALL)
    
    # Convertir código inline
    html_content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html_content, flags=re.DOTALL)
    
    # Convertir listas
    html_content = re.sub(r'<ul[^>]*>', '\n', html_content)
    html_content = re.sub(r'</ul>', '\n', html_content)
    html_content = re.sub(r'<ol[^>]*>', '\n', html_content)
    html_content = re.sub(r'</ol>', '\n', html_content)
    html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html_content, flags=re.DOTALL)
    
    # Convertir párrafos
    html_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html_content, flags=re.DOTALL)
    
    # Convertir enlaces
    html_content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html_content, flags=re.DOTALL)
    
    # Convertir negrita y cursiva
    html_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html_content, flags=re.DOTALL)
    
    # Convertir blockquotes
    html_content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', html_content, flags=re.DOTALL)
    
    # Convertir líneas horizontales
    html_content = re.sub(r'<hr[^>]*/?>', '\n---\n', html_content)
    
    # Convertir saltos de línea
    html_content = re.sub(r'<br[^>]*/?>', '\n', html_content)
    
    # Convertir tablas (básico)
    html_content = re.sub(r'<table[^>]*>', '\n', html_content)
    html_content = re.sub(r'</table>', '\n', html_content)
    html_content = re.sub(r'<tr[^>]*>', '', html_content)
    html_content = re.sub(r'</tr>', ' |\n', html_content)
    html_content = re.sub(r'<th[^>]*>(.*?)</th>', r'| **\1** ', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<td[^>]*>(.*?)</td>', r'| \1 ', html_content, flags=re.DOTALL)
    
    # Remover divs y spans
    html_content = re.sub(r'<div[^>]*>', '\n', html_content)
    html_content = re.sub(r'</div>', '\n', html_content)
    html_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', html_content, flags=re.DOTALL)
    
    # Remover todas las demás etiquetas HTML
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Decodificar entidades HTML comunes
    html_content = html_content.replace('&lt;', '<')
    html_content = html_content.replace('&gt;', '>')
    html_content = html_content.replace('&amp;', '&')
    html_content = html_content.replace('&quot;', '"')
    html_content = html_content.replace('&#39;', "'")
    html_content = html_content.replace('&nbsp;', ' ')
    html_content = html_content.replace('&ndash;', '–')
    html_content = html_content.replace('&mdash;', '—')
    html_content = html_content.replace('&copy;', '©')
    html_content = html_content.replace('&reg;', '®')
    
    # Limpiar múltiples líneas vacías
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    
    # Limpiar espacios al inicio de líneas
    html_content = re.sub(r'\n[ \t]+', '\n', html_content)
    
    return html_content.strip()


def extract_language(class_name: str) -> str:
    """Extrae el lenguaje de programación de una clase CSS"""
    # Patrones comunes: language-python, lang-js, highlight-python
    patterns = [
        r'language-(\w+)',
        r'lang-(\w+)',
        r'highlight-(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, class_name)
        if match:
            return match.group(1)
    
    return ""


def truncate_text(text: str, max_length: int = 10000) -> str:
    """Trunca texto largo manteniendo palabras completas"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    # Cortar en el último espacio para no cortar palabras
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    
    return truncated + "\n\n... [contenido truncado]"
