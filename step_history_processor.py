from firestore_service import FirestoreService
import logging
import pandas as pd

class StepHistoryProcessor:
    ''' Processes the step history df from firestore, creating summary dataframes for plotting
    '''

    def __init__(self, step_history_df):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        self.step_history_df = step_history_df

    def _create_week_to_yesterday_df(self):
        ''' Returns a df with dates (2024-10-19 format) and day_of_week
        for a full week up to yesterday
        Columns: date (datetime64[ns]), and day_of_week (string)
        '''
        start_of_week_to_yesterday = pd.Timestamp.now() - pd.DateOffset(days=7)
        end_of_week_to_yesterday = pd.Timestamp.now() - pd.DateOffset(days=1)
        date_range = pd.date_range(start=start_of_week_to_yesterday, end=end_of_week_to_yesterday)

        df = pd.DataFrame({
            'date': date_range.strftime('%Y-%m-%d'),  # Format the date as 'YYYY-MM-DD'
            'day_of_week': date_range.strftime('%A')  # Get the day of the week name
        })
        df['date'] = pd.to_datetime(df['date'])

        return df.copy()
    
    def filter_3m_to_date(self):
        ''' Step history (steps per day) from 3 months ago
        Columns: date (datetime64[ns]), and day_of_week (string), step_count (int)
        '''
        df = self.step_history_df.copy()
        date_3m_ago = pd.Timestamp.now() - pd.DateOffset(months=3)
        
        df_3m = df[df['date'] > date_3m_ago]
        df_3m['day_of_week'] = df_3m['date'].dt.day_name()
        return df_3m.copy()

    def create_3m_avg_by_weekday(self):
        ''' Average steps per day, by weekday for the past 3 months
        Columns: day_of_week (string), 3m_avg (int)
        '''
        df_3m = self.filter_3m_to_date()

        df_3m_grouped = df_3m.groupby('day_of_week')['step_count'].mean().astype(int).reset_index()
        df_3m_grouped = df_3m_grouped.rename(columns={'step_count': '3m_avg'})
        return df_3m_grouped.copy()

    def create_last_week_summary_by_day(self):
        ''' Step history summary for last week
        Columns: date (datetime64[ns]), day_of_week (string), step_count (int), 3m_avg (int)
        '''
        df_last_week = self._create_week_to_yesterday_df()
        df_last_week = pd.merge(df_last_week, self.step_history_df, how='left', on='date')

        df_3m_by_weekday = self.create_3m_avg_by_weekday().copy()

        df_last_week = pd.merge(df_last_week, df_3m_by_weekday, how='left', on='day_of_week')
        return df_last_week.copy()

    def filter_year_to_date(self):
        ''' Return step_history df from one year ago
        '''
        df = self.step_history_df.copy()
        one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
        df = df[df["date"] > one_year_ago]
        return df

    def get_year_to_date_avg_step_count(self):
        ''' Average steps per day from one year ago
        '''
        df = self.filter_year_to_date()
        avg_step_count = int(df["step_count"].mean())
        return avg_step_count

    def create_year_to_date_by_week(self):
        '''
        Colums: week, step_count_avg
        '''
        df = self.filter_year_to_date()
        df['week'] = df['date'].dt.to_period('W')
        ytd_df = df.groupby('week')['step_count'].mean().astype(int).reset_index()
        ytd_df.rename(columns={"step_count":"step_count_avg"}, inplace=True)

        return ytd_df
    
    def create_year_to_date_by_month(self):
        df = self.filter_year_to_date()
        df['week'] = df['date'].dt.to_period('M')
        ytd_df = df.groupby('week')['step_count'].mean().astype(int).reset_index()
        ytd_df.rename(columns={"step_count":"step_count_avg"}, inplace=True)

        return ytd_df
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_history_processor = StepHistoryProcessor(step_history_df)

    ytd_avg = step_history_processor.get_year_to_date_avg_step_count()
    print(f"Year to date average step count: {ytd_avg}")
    ytd_by_week = step_history_processor.create_year_to_date_by_week()
    print(ytd_by_week)

    ytd_by_month = step_history_processor.create_year_to_date_by_month()
    print(ytd_by_month)

    
