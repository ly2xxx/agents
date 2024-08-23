# Embedding Streamlit Pages in Other Streamlit Pages

Streamlit is a powerful framework for building interactive web applications using Python. As applications grow in complexity, developers often face the challenge of managing multiple pages within a single app. Fortunately, Streamlit has introduced native support for multipage applications, allowing you to easily embed pages within one another. This article will guide you through the process of embedding Streamlit pages, using various methods and best practices.

## 1. Creating a Multipage Streamlit App

To start building a multipage Streamlit application, you can follow these steps:

### Step-by-Step Guide

1. **Create a Main Script**: Begin by creating a main script named `streamlit_app.py`.

2. **Organize Your Files**: In the same directory, create a folder named `pages`. This will house your additional pages.

3. **Add New Pages**: Inside the `pages` folder, create new Python files for each additional page. For example:
   ```
   my_app/
   ├── streamlit_app.py  # Your main script
   └── pages/
       ├── page_2.py     # New page 2
       └── page_3.py     # New page 3
   ```

4. **Run Your App**: Execute the app by running:
   ```bash
   streamlit run streamlit_app.py
   ```

The `streamlit_app.py` script will be your main page, with additional scripts appearing in the sidebar for navigation.

### Converting an Existing App

If you have an existing Streamlit app that uses mechanisms like `st.selectbox` to switch between pages, you can convert it into a multipage app by following these steps:

1. **Upgrade Streamlit**: Ensure you are using the latest version:
   ```bash
   pip install --upgrade streamlit
   ```

2. **Create the `pages` Folder**: As described above, create the `pages` folder and move your existing page functions into their respective files.

3. **Modify Your Main Script**: Remove the select box logic and simply structure your functions in separate files.

### Example Code

Here’s a simple example to illustrate how this looks:

```python
# Contents of ~/my_app/streamlit_app.py
import streamlit as st

def main_page():
    st.markdown("# Main page 🎉")

def page2():
    st.markdown("# Page 2 ❄️")

def page3():
    st.markdown("# Page 3 🎈")

# The main page will be rendered automatically by Streamlit's multipage support.
```

## 2. Embedding Streamlit Apps

### Using iFrames

Streamlit allows you to embed public apps into other platforms (like blogs or documentation) using iframes. To embed a Streamlit app, you can append `/?embed=true` to your app's URL. For example:

```html
<iframe src="https://yourapp.streamlit.app/?embed=true" style="height: 450px; width: 100%;"></iframe>
```

**What Happens When You Embed?**
- The toolbar, padding, footer, and colored line are removed, providing a cleaner appearance.

### Using oEmbed

For platforms that support oEmbed (like Medium or Notion), you can simply paste the Streamlit app URL directly into your content. The app will render automatically without needing to modify the URL.

### Key Differences Between iFrame and oEmbed
- **iFrames**: Offer customization options (like hiding the toolbar).
- **oEmbed**: Simpler to use; just paste the URL.

## 3. Managing State Between Pages

When developing multipage apps, you might want to maintain state across pages. This can be achieved by leveraging Streamlit's session state. For enhanced functionality, consider using third-party libraries like `streamlit-multipage`, which allows for state persistence across pages.

### Example of State Management

```python
import streamlit as st
from streamlit_multipage import MultiPage

def input_page(st, **state):
    st.title("Input Page")
    weight = st.number_input("Weight (Kg):", value=state.get("weight", 0.0))
    height = st.number_input("Height (m):", value=state.get("height", 0.0))
    if weight and height:
        MultiPage.save({"weight": weight, "height": height})

def compute_page(st, **state):
    st.title("BMI Result")
    weight = state.get("weight")
    height = state.get("height")
    if weight and height:
        st.metric("BMI", round(weight / (height ** 2), 2))
    else:
        st.warning("Please provide your weight and height on the Input Page.")

app = MultiPage()
app.add_app("Input Page", input_page)
app.add_app("Compute BMI", compute_page)
app.run()
```

## 4. Leveraging the `st.Page` API

With the latest versions of Streamlit, you can use the `st.Page` API to define and navigate between pages programmatically. Here’s how you can utilize this feature:

```python
import streamlit as st

def second_page():
    st.title("This is the second page!")

page = st.navigation([
    st.Page("first_page.py", title="First Page"),
    st.Page(second_page, title="Second Page"),
])
page.run()
```

This allows you to define your pages in a more structured manner, making it easier to manage navigation and page content.

## Conclusion

Embedding pages within Streamlit apps can significantly enhance user experience and application functionality. By following the methods outlined above, you can create multipage applications that are not only interactive but also maintain state across different views. Whether you choose to embed apps externally or develop a multipage setup internally, Streamlit provides the necessary tools to build effective and engaging web applications.

URL: https://elc.github.io/posts/streamlit-multipage/ - fetched successfully.
URL: https://blog.streamlit.io/introducing-multipage-apps/ - fetched successfully.
URL: https://docs.streamlit.io/develop/api-reference/navigation/st.page - fetched successfully.
URL: https://github.com/Sven-Bo/streamlit-multipage-app-example - fetched successfully.
URL: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app/embed-your-app - fetched successfully.