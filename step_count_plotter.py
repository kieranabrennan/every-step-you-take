from firestore_service import FirestoreService
import logging
import pandas as pd
import matplotlib.pyplot as plt

class StepCountPlotter:
    ''' Calculates summary metrics and plots 
    '''
    def __init__(self, step_history_df):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.step_history_df = step_history_df

    def _create_week_to_yesterday_dates(self):
        ''' Returns a df with dates (2024-10-19 format) and day_of_week
        for a full week up to yesterday
        '''
        start_of_week_to_yesterday = pd.Timestamp.now() - pd.DateOffset(days=7)
        end_of_week_to_yesterday = pd.Timestamp.now() - pd.DateOffset(days=1)
        date_range = pd.date_range(start=start_of_week_to_yesterday, end=end_of_week_to_yesterday)

        df = pd.DataFrame({
            'date': date_range.strftime('%Y-%m-%d'),  # Format the date as 'YYYY-MM-DD'
            'day_of_week': date_range.strftime('%A')  # Get the day of the week name
        })
        df['date'] = pd.to_datetime(df['date'])

        return df
    
    def _create_last_week_summary_df(self):
        ''' Creates dataframe of
        Columns: date, day_of_week, step_count, 3m_avg
        '''
        df_last_week = self._create_week_to_yesterday_dates()
        df_last_week = pd.merge(df_last_week, self.step_history_df, how='left', on='date')

        dates_3m = pd.Timestamp.now() - pd.DateOffset(months=3)
        df_3m = self.step_history_df[self.step_history_df['date'] > dates_3m].copy()
        df_3m['day_of_week'] = df_3m['date'].dt.day_name()

        df_3m_grouped = df_3m.groupby('day_of_week')['step_count'].mean().astype(int).reset_index()
        df_3m_grouped = df_3m_grouped.rename(columns={'step_count': '3m_avg'})

        df_last_week = pd.merge(df_last_week, df_3m_grouped, how='left', on='day_of_week')
        return df_last_week

    def plot_last_week_steps(self, display=True):
        ''' Plots steps per day for the week up to yesterday
        Along with average over last 3 months
        '''
        
        df_last_week = self._create_last_week_summary_df()

        # Choose pretty colors for the lines
        solid_line_color = '#1f77b4'  # A nice blue color
        dotted_line_color = '#ff7f0e'  # A nice orange color

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df_last_week['day_of_week'], df_last_week['step_count'], linestyle='-', color=solid_line_color, label='Weekly Avg')
        ax.plot(df_last_week['day_of_week'], df_last_week['3m_avg'], linestyle='--', color=dotted_line_color, label='3-Month Avg')

        def format_steps(steps):
            if abs(steps) >= 1000:
                return f"{steps / 1000:.1f}k"
            else:
                return str(steps)

        # Set the title with colored text
        title = (f'Week avg.: {format_steps(int(df_last_week['step_count'].mean()))} steps/day\n')

        ax.set_title(f'{title}', loc='center', fontsize=10, color=solid_line_color, pad=10)
        ax.text(0.5, 1.02, f'3-month avg: {format_steps(int(df_last_week['3m_avg'].mean()))} steps/day', 
                    fontsize=10, color=dotted_line_color, ha='center', va='bottom', transform=plt.gca().transAxes)

        # Set labels
        ax.set_ylabel('Steps per day')
        ax.set_ylim([0, max(df_last_week['step_count'].max(), 12000)]) 
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels(ax.get_xticklabels(), rotation=15)
        fig.tight_layout()
        
        if display:
            plt.show()
            
        return fig
            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_count_plotter = StepCountPlotter(step_history_df)
    fig = step_count_plotter.plot_last_week_steps()


    