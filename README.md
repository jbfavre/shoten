# Shoten

This project aims to ease container inspection and security management.  
It inspects distribution packages dependencies (currently Debian) and store them in a graph database (currently Neo4j).

Adding your container's images into the graph database allows you to register which package is installed on which image.  
Therefore, you're able to easily spot which image needs to be rebuild after a package update.

You can also identify PODs to restart based on which image they use.

## Installation

### Neo4j

### Python requirements

Shoten uses:

- python-apt

## The name

Shoten, or Shoten sama, is the japanese name of Ganesh. He's seen as the god of happiness.  
In hindouism, Ganesh is the god who remove obstacles, which is pretty what I wanted to achieve with this project :)
