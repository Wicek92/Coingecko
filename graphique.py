import streamlit as st
import pandas as pd
import numpy as np

data = pd.DataFrame(np.random.randn(10, 2), columns=["x", "y"])
st.line_chart(data)
