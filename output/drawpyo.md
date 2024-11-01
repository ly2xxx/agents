# Drawpyo: A Python Library for Generating Draw.io Diagrams

## Introduction

Drawpyo is a powerful Python library designed for programmatically generating diagrams using Draw.io (also known as Diagrams.net). This library allows users to create, style, and save diagrams in a straightforward manner, making it an excellent tool for developers and technical writers who need to automate diagram creation.

## Key Features

- **Programmatic Diagram Creation**: Users can create diagrams by writing Python code, which is particularly useful for generating diagrams from data or specifications.
- **Integration with Draw.io**: Drawpyo leverages the capabilities of Draw.io, allowing users to create diagrams that can be opened and edited in the Draw.io application.
- **XML-Based File Format**: Diagrams are saved in a plaintext XML format, making them easy to version control alongside code in repositories.

## Installation

To install Drawpyo, you can use pip:

```bash
pip install drawpyo
```

## Basic Usage

### Creating a New Diagram

To create a new diagram, you need to initialize a `File` object and add pages and objects to it. Here’s a simple example:

```python
import drawpyo

# Create a new file
file = drawpyo.File()
file.file_path = r"C:\drawpyo"
file.file_name = "Test Generated Edges.drawio"

# Add a page
page = drawpyo.Page(file=file)

# Add an object
item = drawpyo.diagram.Object(page=page, value="new object")
item.position = (0, 0)

# Write the file
file.write()
```

### Styling Objects

Drawpyo allows you to style objects using built-in styles or custom style strings. Here’s how to apply a style:

```python
item_from_stylestr = drawpyo.diagram.Object(page=page)
item_from_stylestr.apply_style_string("rounded=1;whiteSpace=wrap;html=1;fillColor=#6a00ff;fontColor=#ffffff;strokeColor=#000000;gradientColor=#FF33FF;strokeWidth=4;")
```

### Creating Tree Diagrams

Drawpyo also supports specific diagram types, such as tree diagrams. Here’s an example of how to create a tree diagram:

```python
from drawpyo.diagram_types import TreeDiagram, NodeObject

# Create a new tree diagram
tree = TreeDiagram(file_path="C:\\drawpyo", file_name="Coffee Grinders.drawio", direction="down", link_style="orthogonal")

# Create NodeObjects
grinders = NodeObject(tree=tree, value="Appliances for Grinding Coffee", base_style="rounded rectangle")
blade_grinders = NodeObject(tree=tree, value="Blade Grinders", tree_parent=grinders)
burr_grinders = NodeObject(tree=tree, value="Burr Grinders", tree_parent=grinders)

# Auto layout and write the diagram
tree.auto_layout()
tree.write()
```

## Resources for Learning Drawpyo

1. **Official Documentation**: The [Drawpyo Documentation](https://merrimanind.github.io/drawpyo/) provides comprehensive guides and examples on how to use the library effectively.
2. **GitHub Repository**: The [Drawpyo GitHub Repository](https://github.com/MerrimanInd/drawpyo) contains the source code, example scripts, and community contributions.
3. **Basic Usage Guide**: A dedicated page for [Basic Usage of Drawpyo](https://merrimanind.github.io/drawpyo/usage/basic_usage/) outlines fundamental functionalities and provides code snippets.
4. **Example Scripts**: You can find specific example scripts, such as [Building a Flowchart](https://github.com/MerrimanInd/drawpyo/blob/main/etc/development+scripts/build_a_flowchart.py), which demonstrate practical applications of the library.

## Conclusion

Drawpyo is a versatile library that simplifies the process of creating diagrams programmatically in Python. With its integration with Draw.io, users can generate high-quality diagrams that are easy to manage and version control. Whether you are a developer looking to automate documentation or a technical writer needing to create diagrams from specifications, Drawpyo offers the tools you need to succeed.