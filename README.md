# Aplicación con GUI para controlar una impresora MEW de alta tensión con cabezal de extrusión de pellets

Este repositorio contiene una aplicación personalizada en Python desarrollada para controlar una impresora de melt electrowriting (MEW) de forma centralizada. El objetivo principal de esta aplicación es unificar el control de todos los sistemas eléctricos y electrónicos de la impresora en una única interfaz, facilitando su manejo.
<p align="center">
<img src="images/MEW%20anuar.jpg" width="200"/>
</p>

## Conexión de Dispositivos

Se ha diseñado una interfaz específica que permite controlar tanto el caudal como la temperatura de impresión del extrusor, además de gestionar la velocidad y los movimientos de la etapa posicionadora desde un único panel. La interfaz se organiza en dos áreas principales: una cinta de opciones superior y otra lateral. La cinta de opciones superior permite establecer la comunicación serie con los diferentes elementos de la máquina conectados a través de USB.

<p align="center">
<img src="images/Figura%2021.1.png" width="600"/>
</p>

<p align="center">
<img src="images/Figura%2021.2.png" width="600"/>
</p>

<p align="center">
<img src="images/Figura%2021.3.png" width="600"/>
</p>

## Modo de Impresión Manual

Una vez completada la conexión serie de los elementos y la calibración de las etapas posicionadoras, es posible iniciar la impresión en el modo manual. Este modo ofrece un control completo de los parámetros del proceso mediante botones y entradas de texto.

<p align="center">
<img src="images/Figura%2021.4.png" width="600"/>
</p>

## Modo de Impresión Automático

Se ha implementado un modo automático que permite al usuario seleccionar entre diferentes opciones de impresión, como la calibración de velocidad del sustrato, calibración de la tensión, impresión de un andamio 2D y la impresión de un andamio 3D.

<p align="center">
<img src="images/Figura%2021.5.png" width="600"/>
</p>

## Modo de Impresión con GCode

La aplicación cuenta con una función que permite traducir comandos GCode al lenguaje utilizado por los controladores de la impresora. Para acceder a esta función, el usuario debe dirigirse al menú "GCode".

<p align="center">
<img src="images/Figura%2021.6.png" width="600"/>
</p>

## Authors

- [Anuar R. Giménez El Amrani](https://www.github.com/anuargimenez)

  ([Escuela Técnica Superior de Ingeniería Industrial de Béjar, USAL](https://industriales.usal.es/))
