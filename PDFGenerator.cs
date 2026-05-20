using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
Document.Create(container =>
{
   container.Page(page =>
   {
       page.Margin(1, Unit.Centimetre);
       page.PageSize(PageSizes.A4);
       // Configurar tipo de letra global por defecto (ej. Helvetica, Arial, Roboto)
       page.DefaultTextStyle(x => x.FontFamily("Arial").FontSize(11));
       page.Content().Column(column =>
       {
           // 1. TÍTULO CON FUENTES, COLORES Y TIPOS DE LETRA (Bold/Italic)
           column.Item().Text(text =>
           {
               text.Line("1. Especificaciones de Operación")
                   .FontSize(22)
                   .Bold()
                   .FontColor("#002855"); // Azul industrial (Hexadecimal)
               text.Line("Aviso importante para el operador de planta.")
                   .FontSize(12)
                   .Italic()
                   .FontColor(Colors.Grey.Medium); // Color predefinido
           });
           column.Item().PaddingVertical(10);
           // 2. FORMAS CON Y SIN RELLENO DE COLOR
           // Rectángulo con relleno (Alerta de seguridad)
           column.Item().Background("#FFD2D2").Padding(10).Row(row =>
           {
               row.ConstantItem(5).Background("#D9383A"); // Línea roja vertical (borde izquierdo simulado)
               row.RelativeItem().PaddingLeft(10).Text("¡PELIGRO! Apagar la máquina antes de limpiar.").Bold().FontColor("#D9383A");
           });
           column.Item().PaddingVertical(10);
           // Círculo o Forma sin relleno (Borde estructural o contenedor vacío)
           column.Item().Border(1).BorderColor("#002855").Padding(10).Text("Este es un contenedor con borde estructural sin relleno de fondo.");
           column.Item().PaddingVertical(15);
           // 3. TABLAS AVANZADAS (Con encabezados, bordes y alineación)
           column.Item().Text("Historial de Mantenimiento").FontSize(14).Bold().FontColor("#002855");
           column.Item().PaddingTop(5);
           column.Item().Table(table =>
           {
               // Definir las columnas y sus tamaños proporcionales o constantes
               table.ColumnsDefinition(columns =>
               {
                   columns.ConstantColumn(80);   // Código (Tamaño fijo)
                   columns.RelativeColumn(2);    // Descripción (Toma el doble de espacio)
                   columns.RelativeColumn(1);    // Estado
               });
               // Encabezados de la Tabla (Fila 1)
               table.Header(header =>
               {
                   header.Cell().Background("#002855").Padding(5).Text("Código").Bold().FontColor(Colors.White);
                   header.Cell().Background("#002855").Padding(5).Text("Descripción del Proceso").Bold().FontColor(Colors.White);
                   header.Cell().Background("#002855").Padding(5).Text("Estado").Bold().FontColor(Colors.White);
               });
               // Contenido de la Tabla (Filas de datos)
               // Fila 1
               table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Light).Padding(5).Text("REQ-001");
               table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Light).Padding(5).Text("Verificación visual de la banda transportadora.");
               table.Cell().BorderBottom(0.5f).BorderColor(Colors.Grey.Light).Padding(5).Text("Completado").FontColor(Colors.Green.Medium).Bold();
               // Fila 2 (Con estilo alterno para facilitar la lectura en la industria)
               table.Cell().Background(Colors.Grey.Lighten4).Padding(5).Text("REQ-002");
               table.Cell().Background(Colors.Grey.Lighten4).Padding(5).Text("Calibración del sensor óptico de proximidad.");
               table.Cell().Background(Colors.Grey.Lighten4).Padding(5).Text("Pendiente").FontColor(Colors.Orange.Medium).Bold();
           });
       });
   });
})
.GeneratePdf("resultado.pdf");