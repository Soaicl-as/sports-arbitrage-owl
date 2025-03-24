
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArbitrageFinder:
    def __init__(self):
        pass
    
    def find_arbitrage_opportunities(self, odds_df):
        """Find arbitrage opportunities in the scraped odds data"""
        if odds_df.empty:
            logger.warning("No odds data to analyze")
            return []
        
        opportunities = []
        
        # Group by event and market to compare odds
        grouped = odds_df.groupby(['sport', 'event', 'market'])
        
        for (sport, event, market), group in grouped:
            # Skip groups with only one selection
            if len(group) < 2:
                continue
            
            # Check for arbitrage in different bet types
            if "Moneyline" in market or "Match Winner" in market or "1X2" in market:
                arb_opps = self.check_moneyline_arbitrage(group, sport, event, market)
                opportunities.extend(arb_opps)
            
            elif "Over/Under" in market or "Total" in market:
                arb_opps = self.check_over_under_arbitrage(group, sport, event, market)
                opportunities.extend(arb_opps)
            
            elif "Handicap" in market or "Spread" in market:
                arb_opps = self.check_handicap_arbitrage(group, sport, event, market)
                opportunities.extend(arb_opps)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def check_moneyline_arbitrage(self, group, sport, event, market):
        """Check for arbitrage opportunities in moneyline markets"""
        opportunities = []
        
        # Get unique selections
        selections = group['selection'].unique()
        
        # Check if we have odds for all possible outcomes
        if len(selections) < 2:  # Need at least home and away
            return []
        
        # Extract best odds for each selection
        best_odds = {}
        for selection in selections:
            selection_group = group[group['selection'] == selection]
            if not selection_group.empty:
                best_odds[selection] = {
                    'bookmaker': selection_group.loc[selection_group['odds'].idxmax(), 'bookmaker'],
                    'odds': selection_group['odds'].max()
                }
        
        # Calculate arbitrage opportunity
        arb_sum = sum(1 / odds['odds'] for odds in best_odds.values())
        
        # If sum < 1, we have an arbitrage opportunity
        if arb_sum < 1:
            profit_percentage = (1 - arb_sum) * 100
            
            # Only report meaningful arbitrage opportunities (> 1%)
            if profit_percentage > 1:
                # Calculate optimal stakes for a $1000 total stake
                total_stake = 1000
                stakes = {}
                bets = []
                
                for selection, odds_data in best_odds.items():
                    stake_percentage = (1 / odds_data['odds']) / arb_sum * 100
                    stake_amount = total_stake * stake_percentage / 100
                    expected_return = stake_amount * odds_data['odds']
                    
                    bets.append({
                        'bookmaker': odds_data['bookmaker'],
                        'selection': selection,
                        'odds': odds_data['odds'],
                        'stake_percentage': stake_percentage,
                        'stake_amount': stake_amount
                    })
                
                # Create opportunity object
                opportunity = {
                    'sport': sport,
                    'event': event,
                    'market': market,
                    'bet_type': 'Moneyline',
                    'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'profit_percentage': profit_percentage,
                    'bets': bets,
                    'total_stake': total_stake,
                    'expected_return': total_stake + (total_stake * profit_percentage / 100)
                }
                
                opportunities.append(opportunity)
        
        return opportunities
    
    def check_over_under_arbitrage(self, group, sport, event, market):
        """Check for arbitrage opportunities in over/under markets"""
        opportunities = []
        
        # Group by line value to compare over and under for the same line
        lines = group['selection'].str.extract(r'([\d.]+)').dropna()[0].unique()
        
        for line in lines:
            over_group = group[group['selection'].str.contains(f"Over {line}")]
            under_group = group[group['selection'].str.contains(f"Under {line}")]
            
            if over_group.empty or under_group.empty:
                continue
            
            # Get best over and under odds
            best_over_idx = over_group['odds'].idxmax()
            best_under_idx = under_group['odds'].idxmax()
            
            best_over = {
                'bookmaker': over_group.loc[best_over_idx, 'bookmaker'],
                'selection': over_group.loc[best_over_idx, 'selection'],
                'odds': over_group.loc[best_over_idx, 'odds']
            }
            
            best_under = {
                'bookmaker': under_group.loc[best_under_idx, 'bookmaker'],
                'selection': under_group.loc[best_under_idx, 'selection'],
                'odds': under_group.loc[best_under_idx, 'odds']
            }
            
            # Calculate arbitrage
            arb_sum = (1 / best_over['odds']) + (1 / best_under['odds'])
            
            if arb_sum < 1:
                profit_percentage = (1 - arb_sum) * 100
                
                # Only report meaningful arbitrage opportunities (> 1%)
                if profit_percentage > 1:
                    # Calculate optimal stakes for a $1000 total stake
                    total_stake = 1000
                    
                    over_stake_percentage = (1 / best_over['odds']) / arb_sum * 100
                    over_stake_amount = total_stake * over_stake_percentage / 100
                    
                    under_stake_percentage = (1 / best_under['odds']) / arb_sum * 100
                    under_stake_amount = total_stake * under_stake_percentage / 100
                    
                    bets = [
                        {
                            'bookmaker': best_over['bookmaker'],
                            'selection': best_over['selection'],
                            'odds': best_over['odds'],
                            'stake_percentage': over_stake_percentage,
                            'stake_amount': over_stake_amount
                        },
                        {
                            'bookmaker': best_under['bookmaker'],
                            'selection': best_under['selection'],
                            'odds': best_under['odds'],
                            'stake_percentage': under_stake_percentage,
                            'stake_amount': under_stake_amount
                        }
                    ]
                    
                    # Create opportunity object
                    opportunity = {
                        'sport': sport,
                        'event': event,
                        'market': market,
                        'bet_type': f'Over/Under {line}',
                        'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'profit_percentage': profit_percentage,
                        'bets': bets,
                        'total_stake': total_stake,
                        'expected_return': total_stake + (total_stake * profit_percentage / 100)
                    }
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    def check_handicap_arbitrage(self, group, sport, event, market):
        """Check for arbitrage opportunities in handicap/spread markets"""
        opportunities = []
        
        # Extract handicap values using regex
        group['handicap'] = group['selection'].str.extract(r'([+-]?[\d.]+)').astype(float)
        
        # Get unique handicap values
        handicaps = group['handicap'].unique()
        
        for handicap in handicaps:
            # Find the opposite handicap (e.g., +2.5 and -2.5)
            opposite_handicap = -handicap
            
            team1_group = group[group['handicap'] == handicap]
            team2_group = group[group['handicap'] == opposite_handicap]
            
            if team1_group.empty or team2_group.empty:
                continue
            
            # Get best odds for each team
            best_team1_idx = team1_group['odds'].idxmax()
            best_team2_idx = team2_group['odds'].idxmax()
            
            best_team1 = {
                'bookmaker': team1_group.loc[best_team1_idx, 'bookmaker'],
                'selection': team1_group.loc[best_team1_idx, 'selection'],
                'odds': team1_group.loc[best_team1_idx, 'odds']
            }
            
            best_team2 = {
                'bookmaker': team2_group.loc[best_team2_idx, 'bookmaker'],
                'selection': team2_group.loc[best_team2_idx, 'selection'],
                'odds': team2_group.loc[best_team2_idx, 'odds']
            }
            
            # Calculate arbitrage
            arb_sum = (1 / best_team1['odds']) + (1 / best_team2['odds'])
            
            if arb_sum < 1:
                profit_percentage = (1 - arb_sum) * 100
                
                # Only report meaningful arbitrage opportunities (> 1%)
                if profit_percentage > 1:
                    # Calculate optimal stakes for a $1000 total stake
                    total_stake = 1000
                    
                    team1_stake_percentage = (1 / best_team1['odds']) / arb_sum * 100
                    team1_stake_amount = total_stake * team1_stake_percentage / 100
                    
                    team2_stake_percentage = (1 / best_team2['odds']) / arb_sum * 100
                    team2_stake_amount = total_stake * team2_stake_percentage / 100
                    
                    bets = [
                        {
                            'bookmaker': best_team1['bookmaker'],
                            'selection': best_team1['selection'],
                            'odds': best_team1['odds'],
                            'stake_percentage': team1_stake_percentage,
                            'stake_amount': team1_stake_amount
                        },
                        {
                            'bookmaker': best_team2['bookmaker'],
                            'selection': best_team2['selection'],
                            'odds': best_team2['odds'],
                            'stake_percentage': team2_stake_percentage,
                            'stake_amount': team2_stake_amount
                        }
                    ]
                    
                    # Create opportunity object
                    opportunity = {
                        'sport': sport,
                        'event': event,
                        'market': market,
                        'bet_type': f'Handicap/Spread ({handicap})',
                        'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'profit_percentage': profit_percentage,
                        'bets': bets,
                        'total_stake': total_stake,
                        'expected_return': total_stake + (total_stake * profit_percentage / 100)
                    }
                    
                    opportunities.append(opportunity)
        
        return opportunities
