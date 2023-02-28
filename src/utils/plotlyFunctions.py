import json
import plotly
import plotly.figure_factory as ff
import plotly.express as px
from EDA.functions_EDA.eda_operations import EDA

from logger import logging

class Plotly_agent:
    
    @staticmethod
    def plot_barplot(df, x, y):
        try:
            fig = px.bar(df, x=x, y=y)
            graphJSON = fig.to_json()
            logging.info("BarPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_pieplot(df, names, values, title=''):
        try:
            fig = px.pie(df, names=names, values=values, title=title)
            graphJSON = fig.to_json()
            logging.info("PiePlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    def create_distplot(hist_data, group_labels):
        try:
            fig = ff.create_distplot(hist_data, group_labels, bin_size=1.0,curve_type="kde")
            graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            logging.info("BarPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_distplot(df,x,y,**kwargs):
        try:
            fig = px.histogram(df, x=x, y=y, **kwargs)
            graphJSON = fig.to_json()
            logging.info("Distplot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_scatterplot(df, x, y, **kwargs):
        try:
            fig = px.scatter(df, x=x, y=y,**kwargs)
            graphJSON = fig.to_json()
            logging.info("ScatterPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)
    
    @staticmethod
    def plot_histogram(df, x, bin=20):
        try:
            fig = px.histogram(df, x=x, nbins=bin)
            graphJSON = fig.to_json()
            logging.info("Histogram Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_lineplot(df, x, y):
        try:
            fig = px.line(df, x=x, y=y)
            graphJSON = fig.to_json()
            logging.info("linePlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_boxplot(df, x, y):
        try:
            fig = px.box(df, x=x, y=y)
            graphJSON = fig.to_json()
            logging.info("BoxPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)
            
    @staticmethod
    def boxplot_single(df, x):
        try:
            fig = px.box(df, x=x)
            graphJSON = fig.to_json()
            logging.info("Single BoxPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_pairplot(df,**kwargs):
        try:
            fig = px.scatter_matrix(df,**kwargs)
            fig.update_layout(autosize=False,width=1000,height=1050)
            graphJSON = fig.to_json()
            logging.info("Pairplot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)

    @staticmethod
    def plot_violinplot(df,y):
        try:
            fig = px.violin(df, y=y,points='all')
            graphJSON = fig.to_json()
            logging.info("ViolinPlot Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)


    @staticmethod
    def show_heatmap(df):
        try:
            pearson_corr = EDA.correlation_report(df, 'pearson')
            fig = px.imshow(pearson_corr)
            graphJSON = fig.to_json()
            logging.info("Heatmap Implemented!")
            return graphJSON
        except Exception as e:
            logging.error(e)