"""
main.py - 自助式数据分析（数据分析智能体）

Author: 骆昊
Version: 0.1
Date: 2025/6/25
"""
import random
import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
import streamlit as st
from langchain_openai import OpenAI

from utils import datafr, dataframe_agent
from common import get_llm_response


def create_chart(input_data, chart_type):
    """生成统计图表"""
    df_data = pd.DataFrame(
        data={
            "x": input_data["columns"],
            "y": input_data["data"]
        }
    ).set_index("x")
    if chart_type == "bar":
        plt.figure(figsize=(8, 5), dpi=120)
        plt.bar(input_data["columns"], input_data["data"], width=0.4, hatch='///')
        plt.title("柱状图", fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt.gcf())
    elif chart_type == "line":
        st.line_chart(df_data)
    elif chart_type == "pie":
        plt.figure(figsize=(8, 6), dpi=120)
        plt.pie(input_data["data"], labels=input_data["columns"], autopct='%1.1f%%', startangle=90)
        plt.title("饼图", fontsize=14, fontweight='bold')
        plt.axis('equal')  # 确保饼图是圆形的
        st.pyplot(plt.gcf())


def show_data_summary(df):
    """显示数据统计摘要"""
    st.subheader("📊 数据统计摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总行数", df.shape[0])
    
    with col2:
        st.metric("总列数", df.shape[1])
    
    with col3:
        st.metric("缺失值数量", df.isnull().sum().sum())
    
    with col4:
        st.metric("数值列数量", len(df.select_dtypes(include=['number']).columns))
    
    # 数据类型信息
    st.subheader("📋 列信息")
    col_info = pd.DataFrame({
        '列名': df.columns,
        '数据类型': [str(dtype) for dtype in df.dtypes],
        '非空值数量': df.count(),
        '缺失值数量': df.isnull().sum(),
        '缺失率': (df.isnull().sum() / len(df) * 100).round(2).astype(str) + '%'
    })
    st.dataframe(col_info, use_container_width=True)
    
    # 数值列的描述性统计
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        st.subheader("🔢 数值列描述性统计")
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)


def get_answer(question: str):
    """从大模型获取答案
      :param question: 用户的问题
      :return: 迭代器对象
    """
    try:
        client = OpenAI(base_url=base_url,api_key=api_key)
        stream = get_llm_response(client,model=model_name,user_prompt=question,stream=True)
        for chunk in stream:
            yield chunk.choices[0].delta.content or ''
    # 修改get_answer函数的错误处理部分
    except BaseException as e:
        error_msg = f"错误详情: {str(e)}"
        st.error(error_msg)  # 在界面上显示错误
        yield from '暂时无法回答此问题,请检查你的配置是否正确'

# 侧边栏配置
with st.sidebar:
    api_vendor = st.radio(label='请选择服务提供商:', options=['OpenAI','Deepseek'])
    if api_vendor == 'OpenAI':
        base_url = 'https://twapi.openai-hk.com/v1'
        model_options=['gpt-4o-mini','gpt-3.5-turbo','gpt-4o','gpt-4.1-mini','gpt-4.1']
    elif api_vendor == 'Deepseek':
        base_url = 'https://api.deepseek.com'
        model_options =['deepseek-chat','deepseek-reasoner']
    model_name = st.selectbox(label='请选择要使用的模型：',options=model_options)
    api_key = st.text_input(label='请输入你的key：',type='password')

# 页面选择
page = st.radio("请选择功能:", ["聊天助手", "数据分析智能体"])

if page == "聊天助手":
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [('ai','你好，我是你的AI助手，我叫小九')]

    st.write('## 你最好的聊天伙伴')

    if not api_key:
        st.error('请提供访问大模型需要的API KEY！')
        st.stop()

    for role,content in st.session_state['messages']:
        st.chat_message(role).write(content)

    user_input=st.chat_input(placeholder='请输入')

    if user_input:
        _,history = st.session_state['messages'][-1]
        st.session_state['messages'].append(('human',user_input))
        st.chat_message('human').write(user_input)
        with st.spinner('AI正在思考，请耐心等待...'):
            answer = get_answer(f'{history},{user_input}')
            result = st.chat_message('ai').write_stream(answer)
            st.session_state['messages'].append(('ai',result))
else:
    st.write("## 第九组数据分析智能体")
    option = st.radio("请选择数据文件类型:", ("Excel", "CSV"))
    file_type = "xlsx" if option == "Excel" else "csv"
    data = st.file_uploader(f"上传你的{option}数据文件", type=file_type)

    if data:
        if file_type == "xlsx":
            wb = openpyxl.load_workbook(data)
            option = st.radio(label="请选择要加载的工作表：", options=wb.sheetnames)
            st.session_state["df"] = pd.read_excel(data, sheet_name=option)
        else:
            st.session_state["df"] = pd.read_csv(data)
        
        # 显示数据统计摘要
        show_data_summary(st.session_state["df"])
        
        with st.expander("原始数据"):
            st.dataframe(st.session_state["df"])

    query = st.text_area(
        "请输入你关于以上数据集的问题或数据可视化需求：",
        disabled="df" not in st.session_state,
        placeholder="例如：显示销售额前5的产品饼图，或者分析各地区销售趋势"
    )
    button = st.button("生成回答")

    if button and not data:
        st.info("请先上传数据文件")
        st.stop()

    if query:
        with st.spinner("AI正在思考中，请稍等..."):
            result = dataframe_agent(st.session_state["df"], query)
            if "answer" in result:
                st.write(result["answer"])
            if "table" in result:
                st.table(pd.DataFrame(result["table"]["data"],
                                    columns=result["table"]["columns"]))
            if "bar" in result:
                create_chart(result["bar"], "bar")
            if "line" in result:
                create_chart(result["line"], "line")
            if "pie" in result:
                create_chart(result["pie"], "pie")
