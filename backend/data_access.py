import pandas as pd
import os

# Create a shared data access layer
class DataAccessLayer:
    def __init__(self):
        self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
        self.vendors_df = pd.DataFrame()
        self.invoices_df = pd.DataFrame()
        self.gl_entries_df = pd.DataFrame()
        self.treasury_df = pd.DataFrame()

    def load_data(self):
        try:
            self.vendors_df = pd.read_csv(os.path.join(self.data_dir, 'vendor_master.csv'))
            self.invoices_df = pd.read_csv(os.path.join(self.data_dir, 'invoices.csv'))
            self.gl_entries_df = pd.read_csv(os.path.join(self.data_dir, 'gl_journal_entries.csv'))
            self.treasury_df = pd.read_csv(os.path.join(self.data_dir, 'treasury_cashflow.csv'))
            print("Successfully loaded synthetic datasets into memory.")
        except Exception as e:
            print(f"Error loading datasets: {e}")

    def save_invoices(self):
        self.invoices_df.to_csv(os.path.join(self.data_dir, 'invoices.csv'), index=False)
        
    def save_vendors(self):
        self.vendors_df.to_csv(os.path.join(self.data_dir, 'vendor_master.csv'), index=False)

    def save_gl_entries(self):
        self.gl_entries_df.to_csv(os.path.join(self.data_dir, 'gl_journal_entries.csv'), index=False)

# Global instance
dal = DataAccessLayer()
