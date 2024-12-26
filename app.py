import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
import re
from pyecharts.charts import WordCloud, Bar, Pie, Line, Scatter, Radar
from pyecharts.globals import SymbolType
from pyecharts import options as opts
import os
import streamlit.components.v1 as components

# 用于保存临时文件
TEMP_DIR = './temp'
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_text_from_url(url):
    """从URL获取文本内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.body.get_text(strip=True, separator='\n') if soup.body else ''

def preprocess_text(text):
    """文本预处理"""
    text = re.sub(r'<.*?>', '', text)  # 去除HTML标签
    text = re.sub(r'[^\u4e00-\u9fffA-Za-z]', ' ', text)  # 保留汉字和英文字符
    return re.sub(r'\s+', ' ', text).strip()

def segment_and_count(text, stopwords):
    """分词并统计词频"""
    words = [word for word in jieba.cut(text) if word.strip() and word not in stopwords]
    return Counter(words)

def draw_word_cloud(word_counts, filename="wordcloud.html"):
    """绘制词云图"""
    word_cloud = (
        WordCloud()
        .add("", list(word_counts.items()), word_size_range=[20, 100], shape=SymbolType.DIAMOND)
        .set_global_opts(title_opts=opts.TitleOpts(title="词云"))
    )
    word_cloud.render(os.path.join(TEMP_DIR, filename))

def create_chart(chart_type, word_counts, top_n=20):
    """创建图表"""
    top_words = word_counts.most_common(top_n)
    words, counts = zip(*top_words) if top_words else ([], [])

    if chart_type == "垂直条形图":
        chart = (
            Bar()
            .add_xaxis(list(words))
            .add_yaxis("词频", list(counts))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"垂直条形图"),
                yaxis_opts=opts.AxisOpts(name="频率"),
                xaxis_opts=opts.AxisOpts(name="词语", axislabel_opts=opts.LabelOpts(rotate=-15)),
                toolbox_opts=opts.ToolboxOpts(),
                datazoom_opts=[opts.DataZoomOpts()]
            )
        )
    elif chart_type == "水平条形图":
        chart = (
            Bar()
            .add_xaxis(list(words))
            .add_yaxis("词频", list(counts))
            .reversal_axis()
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"水平条形图"),
                xaxis_opts=opts.AxisOpts(name="频率"),
                yaxis_opts=opts.AxisOpts(name="词语"),
                toolbox_opts=opts.ToolboxOpts(),
                datazoom_opts=[opts.DataZoomOpts(orient="vertical")]
            )
        )
    elif chart_type == "饼图":
        chart = (
            Pie()
            .add(
                "",
                list(zip(words, counts)),
                radius=["30%", "60%"],
                center=["50%", "50%"]
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="饼图",
                    pos_left="center",
                    pos_top="top"
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical", pos_top="15%", pos_left="left"
                )
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(
                    formatter="{b}: {c} ({d}%)", position="outside"
                )
            )
        )
    elif chart_type == "折线图":
        chart = (
            Line()
            .add_xaxis(list(words))
            .add_yaxis("词频", list(counts))
            .set_global_opts(title_opts=opts.TitleOpts(title="折线图"))
        )
    elif chart_type == "散点图":
        chart = (
            Scatter()
            .add_xaxis(list(words))
            .add_yaxis("词频", list(counts))
            .set_global_opts(title_opts=opts.TitleOpts(title="散点图"))
        )
    elif chart_type == "雷达图":
        chart = (
            Radar()
            .add_schema(
                schema=[opts.RadarIndicatorItem(name=word, max_=max(counts)) for word in words]
            )
            .add("词频", [list(counts)])
            .set_global_opts(title_opts=opts.TitleOpts(title="雷达图"))
        )
    elif chart_type == "面积图":  # 添加面积图
        chart = (
            Line()
            .add_xaxis(list(words))
            .add_yaxis(
                "词频",
                list(counts),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.5)  # 设置填充颜色透明度
            )
            .set_global_opts(title_opts=opts.TitleOpts(title="面积图"))
        )
    else:
        return None
    return chart

def render_pyechart(chart):
    """渲染图表到Streamlit"""
    if chart:
        components.html(chart.render_embed(), width=1000, height=800)

def main():
    st.title("文章URL文本分析工具")

    url = st.text_input("请输入文章的URL:")

    chart_type = st.sidebar.selectbox(
        "选择图表类型",
        ["词云", "垂直条形图", "水平条形图", "饼图", "折线图", "散点图", "雷达图", "面积图"],  # 添加“面积图”
    )

    if url == "":
        st.warning("请输入有效的URL以进行分析！")  # 提示用户输入URL
    elif st.button("提交"):
        with st.spinner('正在处理...'):
            text = fetch_text_from_url(url)
            processed_text = preprocess_text(text)

            # 加载停用词表
            with open('stopwords.txt', 'r', encoding='utf-8') as f:
                stopwords = set(line.strip() for line in f)

            word_counts = segment_and_count(processed_text, stopwords)
            draw_word_cloud(word_counts)

            st.write("词频最高的20个词：")
            top_words = word_counts.most_common(20)
            for word, count in top_words:
                st.write(f"{word}: {count}")

            if chart_type == "词云":
                st.components.v1.html(open(os.path.join(TEMP_DIR, "wordcloud.html"), 'r', encoding='utf-8').read(), height=600)
            else:
                chart = create_chart(chart_type, word_counts)
                render_pyechart(chart)

if __name__ == "__main__":
    main()
