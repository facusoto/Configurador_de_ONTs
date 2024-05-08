# Configurador de ONTs

*El objetivo es configurar 30 módems al día, pero la configuración manual puede ser un obstáculo. ¿La solución? Automatización.*

## ¿Cómo funciona?

Este proyecto aprovecha la API de Google Sheets, la biblioteca Selenium y Python para su funcionamiento. Es capaz de configurar los siguientes modelos:

| Askey | Mitrastar |
| ----- | --------- |
| RFT3505VW | GPT-2541GNAC |
| RTF8115VW | GPT-2741GNAC |
| RTF8225VW | GPT-2742GNAC |

El proceso es el siguiente: el usuario proporciona las contraseñas de las ONTs en un registro de Google Sheets. Estas contraseñas son obtenidas mediante la API y utilizadas durante la configuración. Durante y al finalizar el proceso, se recopilan datos únicos de la ONT y se registran en la hoja de Google Sheets en la celda correspondiente a la numeración del dispositivo configurado.

## Guía de operación

1. Se requiere una pila de ONTs Movistar de los modelos seleccionados. La cantidad no es relevante.
2. Reiniciar los dispositivos a su configuración de fábrica y conectarlos al cable de fibra óptica y al cable Ethernet de la computadora.
3. Escribir las contraseñas de cada dispositivo en la hoja de Google Sheets correspondiente (Registro).
4. Al presionar "Enter", se solicitará la cantidad de veces que se desea repetir el proceso (indicando cuántos elementos se configurarán).
5. Se solicitará elegir el registro del cual obtener los datos.
6. Se solicitará el número de módem con el que se iniciará el proceso.
7. Una vez completados estos pasos, las contraseñas escritas previamente en la hoja del registro seleccionado en Google Sheets serán obtenidas, y comenzará el proceso de configuración para el dispositivo actualmente conectado.
8. Una vez finalizado el proceso, los datos relacionados con el dispositivo se registrarán en la hoja de Google Sheets y se solicitará presionar "Enter" para continuar con el siguiente dispositivo. Se deben cambiar los cables correctamente antes de proceder.