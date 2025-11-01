import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

@st.cache_resource
def setup_font(font_path: str):
    try:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
        plt.rcParams['axes.unicode_minus'] = False
        return font_prop
    except FileNotFoundError:
        st.error(f"字体文件未找到: {font_path}。请确保该文件与您的应用在同一目录下。")
        return None

def generate_single_plot(variable_to_plot, current_filters, df_cleaned, font_prop, figsize):
    fig, ax = plt.subplots(figsize=figsize)
    
    min_val, max_val = df_cleaned[variable_to_plot].min(), df_cleaned[variable_to_plot].max()

    if min_val == max_val:
        ax.text(0.5, 0.5, '变量值无变化', ha='center', va='center', fontproperties=font_prop)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(variable_to_plot, fontproperties=font_prop, fontsize=12)
        return fig

    sweep_range = np.linspace(min_val, max_val, 100)
    counts = []
    
    base_query_parts = [f"`{col}` >= {threshold}" for col, threshold in current_filters.items() if col != variable_to_plot]
    base_query = " and ".join(base_query_parts)

    for val in sweep_range:
        full_query = f"`{variable_to_plot}` >= {val}"
        if base_query:
            full_query = f"{base_query} and {full_query}"
        
        counts.append(len(df_cleaned.query(full_query)))

    ax.plot(sweep_range, counts, linewidth=2, color="#66CCFB")
    ax.set_title(variable_to_plot, fontproperties=font_prop, fontsize=12)
    ax.set_xlabel("阈值", fontproperties=font_prop, fontsize=10)
    ax.set_ylabel("数量", fontproperties=font_prop, fontsize=10)
    ax.tick_params(axis='x', labelsize=8); ax.tick_params(axis='y', labelsize=8)
    ax.grid(True, linestyle='--', linewidth=0.5); ax.set_xlim(left=min_val)
    
    current_fixed_value = current_filters[variable_to_plot]
    ax.axvline(x=current_fixed_value, color="#EF6394D5", linestyle='--', linewidth=1.5, label=f'当前值: {current_fixed_value:.2f}')
    
    ax.legend(prop=font_prop, fontsize=9)
    plt.tight_layout()
    return fig

def run_app():
    st.set_page_config(layout="wide", page_title="数据阈值调节平台")

    st.title('数据阈值调节平台')
    st.markdown("""
    这是一个交互式数据阈值调节工具，可通过调节不同变量阈值得到符合条件的结果。\n
    **请从侧边栏上传您自己的 Excel 或 CSV 文件来进行分析。**
    """)

    my_font = setup_font('SourceHanSansCN-Medium_0.otf')
    if my_font is None:
        st.stop()

    st.sidebar.header("请上传您的数据文件")
    uploaded_file = st.sidebar.file_uploader(
        "请上传 Excel 或 CSV 文件",
        type=['xlsx', 'csv'] 
    )

    if uploaded_file is None:
        st.info("请在左侧侧边栏上传一个文件以开始分析。")
        st.stop()

    @st.cache_data
    def load_uploaded_data(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)

    df_raw = load_uploaded_data(uploaded_file)
    st.metric(label="原始数据", value=f"{len(df_raw)} 条")
    with st.expander("点击查看原始数据"):
        st.dataframe(df_raw)

    st.sidebar.header('设置筛选阈值')
    st.sidebar.markdown('请拖动滑块设置各项指标的最小值。')

    numeric_cols = [
        '复杂性指数', '中国出口占全球比例', '美国出口占全球比例', 
        '中国出口到美国的量占中国总出口的比例', '美国从中国进口的量占美国总进口的比例',
        '美国出口到中国的量占美国总出口的比例', '中国从美国进口的量占中国总进口的比例'
    ]

    missing_cols = [col for col in numeric_cols if col not in df_raw.columns]
    if missing_cols:
        st.error(f"错误：您上传的文件缺少以下必需的列：{', '.join(missing_cols)}")
        st.stop()

    slider_values = {}
    for col in numeric_cols:
        if pd.api.types.is_numeric_dtype(df_raw[col]):
            min_val = float(df_raw[col].min())
            max_val = float(df_raw[col].max())
            step_val = max(0.01, (max_val - min_val) / 100)
            
            slider_values[col] = st.sidebar.slider(
                label=col,
                min_value=min_val,
                max_value=max_val,
                value=min_val,
                step=step_val
            )

    df_for_plotting = df_raw.dropna(subset=numeric_cols).copy()
    
    query_conditions = [f"`{col}` >= {threshold}" for col, threshold in slider_values.items()]
    df_filtered = df_for_plotting.query(" and ".join(query_conditions)) if query_conditions else df_for_plotting

    st.header('筛选结果概览')
    st.metric(label="符合条件的记录总数", value=f"{len(df_filtered)} 条")

    with st.expander("点击查看详细数据表格", expanded=False):
        st.dataframe(df_filtered)

    st.header('各指标分析')
    st.info('下图展示了当只改变一个指标的阈值时，符合条件的记录数量会如何变化。红线表示您在侧边栏设置的当前阈值。', icon="🔹")

    fig1 = generate_single_plot(numeric_cols[0], slider_values, df_for_plotting, my_font, figsize=(12.2, 3.5))
    st.pyplot(fig1)

    cols_to_plot = numeric_cols[1:]
    for i in range(0, len(cols_to_plot), 2):
        col1, col2 = st.columns(2)
        with col1:
            if i < len(cols_to_plot):
                fig_i = generate_single_plot(cols_to_plot[i], slider_values, df_for_plotting, my_font, figsize=(6, 3.5))
                st.pyplot(fig_i)
        with col2:
            if i + 1 < len(cols_to_plot):
                fig_j = generate_single_plot(cols_to_plot[i+1], slider_values, df_for_plotting, my_font, figsize=(6, 3.5))
                st.pyplot(fig_j)