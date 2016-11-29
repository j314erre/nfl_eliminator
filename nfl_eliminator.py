import math
from selenium import webdriver
from rpm._rpmmodule import prob
from tensor_index_generator import TensorIndexGenerator
from tensorflow.python.framework.tensor_shape import Dimension
from rpmUtils.arch import score
 

def download_data():
    
    data = []
    
    browser =  webdriver.Firefox()
    browser.get('http://projects.fivethirtyeight.com/2016-nfl-predictions/')
    
    
    div_class_weeks = browser.find_elements_by_class_name("week")
    for div_class_week in div_class_weeks:
        div_class_week.click()
        
        
        away_teams = []
        away_probs = []
        home_teams = []
        home_probs = []
        
        
        td_away_teams = browser.find_elements_by_xpath("//tr[@class='away']/td[@class='team']")
        for td_away_team in td_away_teams:
            away_teams.append(str(td_away_team.get_attribute('data-team')))
            
        div_away_probs = browser.find_elements_by_xpath("//div[@class='prob away']")
        for div_away_prob in div_away_probs:
            away_probs.append(float(div_away_prob.text.strip('%'))/100.0)
            
        td_home_teams = browser.find_elements_by_xpath("//tr[@class='home']/td[@class='team']")
        for td_home_team in td_home_teams:
            home_teams.append(str(td_home_team.get_attribute('data-team')))

        div_home_probs = browser.find_elements_by_xpath("//div[@class='prob home']")
        for div_home_prob in div_home_probs:
            home_probs.append(float(div_home_prob.text.strip('%'))/100.0)
            
        assert len(away_teams)==len(home_teams)
        assert len(away_teams)==len(away_probs)
        assert len(away_probs)==len(home_probs)
        
        # choose winners for the week
        winners = []
        for i in range(len(away_teams)):
            home_team = home_teams[i]
            away_team = away_teams[i]
            home_prob = home_probs[i]
            away_prob = away_probs[i]
            
            assert away_prob>0.0 and away_prob<1.0
            assert home_prob>0.0 and home_prob<1.0
            
            if home_prob > away_prob:
                winners.append((home_team, home_prob))
            else:
                winners.append((away_team, away_prob))    
        
        data.append(winners)  
         
    browser.close()
    
    return data

def search_best(data, start, exclude):
    # slice from start week and exclude and sort
    data_subset = []
    for week in data[start-1:]:
        week_subset = []
        for (team, prob) in week:
            if team not in exclude:
                week_subset.append((team, prob))
            
        sorted_week_subset = sorted(week_subset, key=lambda x: x[1], reverse=True)
        print sorted_week_subset
        data_subset.append(sorted_week_subset)
    
    num_weeks = len(data_subset)
    max_indices = [0]*num_weeks
    log_lookup = {}
    for _ in range(1000000):
        
        
        print "Search %s" % [x+1 for x in max_indices]
        
        # check for not enough teams...
        teams = set()
        for i in range(num_weeks):
            for j in range(max_indices[i]+1):
                (team, prob) = data_subset[i][j]
                if team not in teams:
                    teams.add(team)

        if len(teams)>=num_weeks:        
            size = 1
            for dim in max_indices:
                size *= (dim+1)
            
            print "...size {:,d}".format(size)
            
            # search possible picks
            max_score = None
            best_pick = None
            count = 0
            generator = TensorIndexGenerator(max_indices)
            while generator.hasMore():
                count += 1
                if count % 1000000 == 0:
                    print "...searched {:,d}".format(count)
    
                picks = generator.getNext()
                
                # compute score for these picks
                score = 0.0
                seen = set()
                found_repeat = False
                for iweek, pick in enumerate(picks):
                    (team, prob) = data_subset[iweek][pick]
                    if team in seen:
                        found_repeat = True
                        break
    
                    seen.add(team)
                    
                    if prob not in log_lookup:
                        log_lookup[prob] = math.log(prob)
                        
                    score += log_lookup[prob]
                 
                if not found_repeat:                  
                    if max_score is None or score > max_score:
                        max_score = score
                        best_pick = list(picks)
                    
            
            if best_pick is not None:
                probablity = 1.0
                for iweek, ipick in enumerate(best_pick):
                    (team, prob) = data_subset[iweek][ipick]
                    probablity *= prob
                    print "PICK Week %s %s %s" % (iweek+start, team, prob)
                print "PROBABILITY=%s" % probablity
            
                return None
        else:
            print "...only %s teams" % len(teams)
            
        # put highest candidate into max_indices
        max_week_id = None
        max_prob = None
        for week_id in range(num_weeks):
            idx = max_indices[week_id]+1
            
            if idx < len(data_subset[week_id]):
                (team, prob) = data_subset[week_id][idx]
                if max_prob is None or prob>max_prob:
                    max_prob = prob
                    max_week_id = week_id

        max_indices[max_week_id] += 1
    

def main():
    print "DOWNLOADING..."
    data = download_data()
    for week in data:
        print week
     
    exclude = {"GB", "DET", "SEA", "WSH", "NE", "PIT", "CIN", "MIN", "SD", "ARI", "DAL", "BUF"}
     
    print "SEARCHING..."
    search_best(data, len(exclude)+1, exclude)
    
    
    
if __name__ == "__main__":    
    main()
