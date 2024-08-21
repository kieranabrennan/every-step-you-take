from firestore_service import FirestoreService
from step_history_processor import StepHistoryProcessor
import logging

import matplotlib
matplotlib.use('Agg')  # Use 'Agg' backend to avoid GUI issues in cloud environments

import matplotlib.pyplot as plt


def format_steps(steps):
    if abs(steps) >= 1000:
        return f"{steps / 1000:.1f}k"
    else:
        return str(steps)

class StepSummaryPlotter:
    ''' Calculates summary metrics and plots 
    '''
    def __init__(self, step_history_processor: StepHistoryProcessor):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.step_history_processor = step_history_processor

    def create_summary_plot(self):
        ''' Returns figure handle to summary plot
        Weeky summary by day on top
        Year summary by week on bottom
        '''
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6,6)) 

        self.plot_week_summary_by_day(ax1)
        self.plot_year_summary_by_week(ax2)

        plt.subplots_adjust(hspace=0.6)

        return fig

    def plot_week_summary_by_day(self, ax=None):
        ''' Plots steps per day for the week up to yesterday
        Along with average over last 3 months
        '''
        
        df_last_week = self.step_history_processor.create_last_week_summary_by_day()
        avg_steps_last_week = int(df_last_week["step_count"].mean())
        avg_steps_3m = int(df_last_week["3m_avg"].mean())

        if not ax:
            fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df_last_week['day_of_week'], df_last_week['step_count'], 
                marker='o', linestyle='-', linewidth=2,
                color='forestgreen', label='Last week')
        ax.plot(df_last_week['day_of_week'], df_last_week['3m_avg'], 
                marker='o', linestyle='-', linewidth=2,
                color='grey', label='3-Month Avg')

        ax.legend()

        ax.set_title(f'Week avg.: {format_steps(avg_steps_last_week)} steps/day\n3-month avg: {format_steps(avg_steps_3m)} steps/day')
        ax.set_ylabel('Steps per day')
        ax.set_ylim([0, max(df_last_week['step_count'].max()+1000, 12000)]) 


    def plot_year_summary_by_week(self, ax=None):
        ''' Plots avg steps per day for the year by week
        '''
        ytd_by_week_df = self.step_history_processor.create_year_to_date_by_week()
        ytd_avg = self.step_history_processor.get_year_to_date_avg_step_count()

        if not ax:
            fig, ax = plt.subplots(figsize=(8, 4))
        x = ytd_by_week_df['week'].dt.to_timestamp()
        ax.plot(x, ytd_by_week_df['step_count_avg'], marker='o', linestyle='-', 
                color='tomato', linewidth=2)

        ax.set_title(f'Year avg.: {format_steps(ytd_avg)} steps/day')
        ax.set_ylim([0, max(ytd_by_week_df['step_count_avg'].max()+1000, 12000)]) 
        ax.set_ylabel('Avg. steps/day')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_history_processor = StepHistoryProcessor(step_history_df)

    step_count_plotter = StepSummaryPlotter(step_history_processor)
    fig = step_count_plotter.create_summary_plot()

    fig.savefig('summary_plot.png')


    