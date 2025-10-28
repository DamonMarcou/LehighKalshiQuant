import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as stats

class useful_tools:
    
    def __init__(self):
        pass
    def sharpe_ratio(self,returns):
        return np.mean(returns)/np.std(returns)
        
        
    def prob_plot(self, data):
        '''
        data is the return distribution
        '''
        plt.figure(figsize=(6,6))
        stats.probplot(data, dist="norm", plot=plt)
        plt.title("QQ-plot")
        plt.show()
    def visualize_returns(self, returns, log_return=False):
        """
        Visualize the distribution of returns.
        
        Parameters:
        - returns: pd.Series or list/array of returns
        - log_return: bool, whether to convert to log returns before plotting
        """
        # Convert to Pandas Series if needed
        if not isinstance(returns, pd.Series):
            returns = pd.Series(returns)
        
        # Optional log returns
        if log_return:
            returns = (1 + returns).apply(lambda x: np.log(x))  # log(1 + r)
        
        # Set up plotting grid
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Histogram
        sns.histplot(returns, bins=100, kde=False, ax=axes[0,0], color='skyblue')
        axes[0,0].set_title("Histogram of Returns")
        axes[0,0].set_xlabel("Return")
        axes[0,0].set_ylabel("Frequency")
        
        # KDE
        sns.kdeplot(returns, ax=axes[0,1], fill=True, color='salmon')
        axes[0,1].set_title("Density Plot (KDE) of Returns")
        axes[0,1].set_xlabel("Return")
        
        # Boxplot
        sns.boxplot(x=returns, ax=axes[1,0], color='lightgreen')
        axes[1,0].set_title("Boxplot of Returns")
        
        # QQ plot
        stats.probplot(returns, dist="norm", plot=axes[1,1])
        axes[1,1].set_title("QQ Plot vs Normal")
        
        plt.tight_layout()
        plt.show()