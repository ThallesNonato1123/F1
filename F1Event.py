import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import fastf1 as ff1
import os
import seaborn as sns
from fastf1.core import Laps
from fastf1 import utils
from fastf1 import plotting
from datetime import timedelta
from timple.timedelta import strftimedelta
from fastf1 import plotting
from aceleration import compute_accelerations


race_type_enum = {
    'Q': 'Qualifying',
    'R': 'Race',
    'S': 'Sprint Race',
    'SS': 'Sprint Shootout',
    'FP1': 'FP1',
    'FP2': 'FP2',
    'FP3': 'FP3'
}


class F1Event:
    def __init__(self, year, place, modality):
        self.year = year
        self.place = place
        self.modality = modality
        if not os.path.exists('../cache'):
            os.makedirs('../cache')
        ff1.Cache.enable_cache('../cache')
        self.event = ff1.get_session(self.year,self.place,self.modality)
        self.event.load()
        plotting.setup_mpl()

    def get_laps(self, drv:str):
        return self.event.laps.pick_driver(drv)
    
    def get_laps_race(self):
        return self.event.laps
    
    def get_drivers(self):
        return list(self.event.results['Abbreviation'])
    
    def plot_bargraph_times(self):
        list_fastest_laps = list()    
        for drv in self.event.results['Abbreviation']:
                drvs_fastest_lap = self.event.laps.pick_driver(drv).pick_fastest()
                if not pd.isna(drvs_fastest_lap['LapTime']):
                    list_fastest_laps.append(drvs_fastest_lap)
        fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)

        pole_lap = fastest_laps.pick_fastest()
        fastest_laps['LapTimeDelta'] = fastest_laps['LapTime'] - pole_lap['LapTime']
        team_colors = list()
        for index, lap in fastest_laps.iterlaps():
            color = ff1.plotting.team_color(lap['Team'])
            team_colors.append(color)


            
        fig, ax = plt.subplots(figsize=(12, 6.75))
        ax.barh(fastest_laps.index, fastest_laps['LapTimeDelta'],
                color=team_colors, edgecolor='grey')
        ax.set_yticks(fastest_laps.index)
        ax.set_yticklabels(fastest_laps['Driver'])

        # show fastest at the top
        ax.invert_yaxis()

        lap_time_string = strftimedelta(pole_lap['LapTime'], '%m:%s.%ms')

        plt.suptitle(f"{self.event.event['EventName']} {self.year} \n"
                f"Fastest Lap: {lap_time_string} ({pole_lap['Driver']})")
        
    def plot_bargraph_best_sectors(self):
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 6))
        
        self.event.laps['Sector1TimeSeconds'] = self.event.laps['Sector1Time'].dt.total_seconds()
        self.event.laps['Sector2TimeSeconds'] = self.event.laps['Sector2Time'].dt.total_seconds()
        self.event.laps['Sector3TimeSeconds'] = self.event.laps['Sector3Time'].dt.total_seconds()


        # Organize os dados e ordene-os pelo tempo do setor
        sorted_data_s1 = pd.DataFrame(self.event.laps.sort_values(by='Sector1TimeSeconds').drop_duplicates(subset='Driver')[0:8].reset_index())
        sorted_data_s2 = pd.DataFrame(self.event.laps.sort_values(by='Sector2TimeSeconds').drop_duplicates(subset='Driver')[0:8].reset_index())
        sorted_data_s3 = pd.DataFrame(self.event.laps.sort_values(by='Sector3TimeSeconds').drop_duplicates(subset='Driver')[0:8].reset_index())

        # Gráfico 1: Popularidade x Energia com escala logarítmica
        sns.barplot(data=sorted_data_s1, x="Sector1TimeSeconds", y="Driver", ax=axes[0], errorbar=None)
        axes[0].set_title('S1 Time')
        xmin = sorted_data_s1['Sector1TimeSeconds'][0]
        axes[0].set_xlim(xmin=xmin , xmax = sorted_data_s1['Sector1TimeSeconds'][6] + 0.2)

        sns.barplot(data=sorted_data_s2, x="Sector2TimeSeconds", y="Driver", ax=axes[1], errorbar=None)
        axes[1].set_title('S2 Time')
        xmin = sorted_data_s2['Sector2TimeSeconds'][0]
        axes[1].set_xlim(xmin=xmin , xmax = sorted_data_s2['Sector2TimeSeconds'][6]+ 0.2)

        sns.barplot(data=sorted_data_s3, x="Sector3TimeSeconds", y="Driver", ax=axes[2], errorbar=None)
        axes[2].set_title('S3 Time')
        xmin = sorted_data_s3['Sector3TimeSeconds'][0]
        axes[2].set_xlim(xmin=xmin , xmax = sorted_data_s3['Sector3TimeSeconds'][6]+ 0.2)

        plt.show()

        
    def telemetry_between_drivers(self, drv1: str , drv2:str, lap_number:int = None):
        drv1_laps = self.event.laps.pick_driver(drv1)        
        drv2_laps = self.event.laps.pick_driver(drv2)
        circuit_info = self.event.get_circuit_info()


        if lap_number == None:
            drv1_telemetry = drv1_laps.pick_fastest().get_telemetry().add_distance()
            drv2_telemetry = drv2_laps.pick_fastest().get_telemetry().add_distance()
            
            laps_drv_1 = drv1_laps.pick_fastest()
            laps_drv_2 = drv2_laps.pick_fastest()

            lap_time_drv_1 = drv1_laps.pick_fastest()['LapTime']
            lap_time_drv_2 = drv2_laps.pick_fastest()['LapTime']
        else:
            drv1_telemetry = drv1_laps[drv1_laps.LapNumber == lap_number].get_telemetry().add_distance()
            drv2_telemetry = drv2_laps[drv2_laps.LapNumber == lap_number].get_telemetry().add_distance()
    
            laps_drv_1 = drv1_laps[drv1_laps.LapNumber == lap_number]
            laps_drv_2 = drv2_laps[drv2_laps.LapNumber == lap_number]

            lap_time_drv_1 = drv1_laps[drv1_laps.LapNumber == lap_number].reset_index()['LapTime'][0]
            lap_time_drv_2 = drv2_laps[drv2_laps.LapNumber == lap_number].reset_index()['LapTime'][0]

        color_drv1 = ff1.plotting.team_color(drv1_laps['Team'].reset_index(drop = True)[0])
        color_drv2 = ff1.plotting.team_color(drv2_laps['Team'].reset_index(drop = True)[0])
        

        if(color_drv1 == color_drv2):
             color_drv2 = "#B9DCE3"

        delta_time , ref_tel , compare_tel = utils.delta_time(laps_drv_1, laps_drv_2)

        plot_ratios = [1, 3, 2, 2, 2, 2]
        

        fig, ax = plt.subplots(6, gridspec_kw={'height_ratios': plot_ratios}, figsize=(22, 12))
        lap_time_drv1_string = strftimedelta(lap_time_drv_1, '%m:%s.%ms')
        lap_time_drv2_string = strftimedelta(lap_time_drv_2, '%m:%s.%ms')

        plt.suptitle(f"{self.event.event['EventName']} {self.year} \n"
                            f"{drv1} ({lap_time_drv1_string}) vs {drv2} ({lap_time_drv2_string}) ")


        ax[0].plot(ref_tel['Distance'], delta_time, ls='--')
        ax[0].set(ylabel=f"<-- {drv2}  ahead | {drv1} ahead -->")

        ax[1].plot(drv1_telemetry['Distance'],drv1_telemetry['Speed'], label = f'{drv1}', color = color_drv1 )
        ax[1].plot(drv2_telemetry['Distance'], drv2_telemetry['Speed'], label = f'{drv2}', color = color_drv2)
        ax[1].set(ylabel = 'Speed', xlabel = "Distance")
        ax[1].legend(loc = "lower right")
        ax[1].vlines(x=circuit_info.corners['Distance'], ymin=min(drv1_telemetry['Speed'].min(), drv2_telemetry['Speed'].min()) - 20, 
                    ymax=max(drv1_telemetry['Speed'].max(), drv2_telemetry['Speed'].max())+20,
        linestyles='dotted', colors='grey')
        
        for _, corner in circuit_info.corners.iterrows():
            txt = f"T{corner['Number']}{corner['Letter']}"
            ax[1].text(corner['Distance'], min(drv1_telemetry['Speed'].min(), drv2_telemetry['Speed'].min()) -30, txt,
                    va='center_baseline', ha='center', size='small')

        ax[2].plot(drv1_telemetry['Distance'],drv1_telemetry['Throttle'], label = f'{drv1}', color = color_drv1)
        ax[2].plot(drv2_telemetry['Distance'], drv2_telemetry['Throttle'], label = f'{drv2}', color = color_drv2)
        ax[2].set(ylabel = 'Throttle', xlabel = "Distance")
        ax[2].legend(loc = "lower right")

        ax[3].plot(drv1_telemetry['Distance'],drv1_telemetry['Brake'], label = f'{drv1}', color = color_drv1)
        ax[3].plot(drv2_telemetry['Distance'], drv2_telemetry['Brake'], label = f'{drv2}', color = color_drv2)
        ax[3].set(ylabel = 'Brake', xlabel = "Distance")
        ax[3].legend(loc = "lower right")

        ax[4].plot(drv1_telemetry['Distance'],compute_accelerations(drv1_telemetry)[0], label = f'{drv1}', color = color_drv1)
        ax[4].plot(drv2_telemetry['Distance'], compute_accelerations(drv2_telemetry)[0], label = f'{drv2}', color = color_drv2)
        ax[4].set(ylabel = 'Longitudinal Acelerration', xlabel = "Distance")
        ax[4].legend(loc = "lower right")

        ax[5].plot(drv1_telemetry['Distance'],compute_accelerations(drv1_telemetry)[1], label = f'{drv1}', color = color_drv1)
        ax[5].plot(drv2_telemetry['Distance'], compute_accelerations(drv2_telemetry)[1], label = f'{drv2}', color = color_drv2)
        ax[5].set(ylabel = 'Lateral Acelerration', xlabel = "Distance")
        ax[5].legend(loc = "lower right")
    
    def get_telemetry(self, drv1):
        drv1_laps = self.event.laps.pick_driver(drv1)  
        drv1_telemetry = drv1_laps.pick_fastest().get_telemetry().add_distance()
        return drv1_telemetry
    
    def plot_tyre_degredation(self, drv:str = None):
        
        if drv != None:
            tyredev = self.event.laps.pick_driver(drv).pick_quicklaps()
        else:
            tyredev = self.event.laps[self.event.laps.TrackStatus == '1']
        
        tyredev= tyredev[['Compound', 'TyreLife', 'LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']]

        # Each kg of fuel adds 0.03s to laptime. Fuel is 110kg at start of race and 0 at finish
        # Recalculate all lap times to cars with no fuel
        
        nolaps = tyredev.LapNumber.max()
        totfuel = 110
        secperkg = 0.03
        tyredev['Fuel'] = totfuel - (tyredev['LapNumber'] * (totfuel / nolaps))
        tyredev['LapTime'] = tyredev['LapTime'] / np.timedelta64(1, 's') - (secperkg * tyredev['Fuel'])

        # Drop first lap of the race and first track on set of tyres
        tyredev = tyredev[(tyredev.TyreLife > 1) & (tyredev.LapNumber > 1)]

        # Get minimum laptime per [Compound, TyreLife] and count of occurences of this combination
        tyredev = tyredev[['Compound', 'TyreLife', 'LapTime']].groupby(['Compound', 'TyreLife']). \
                agg({'LapTime': ['min', 'count']}).reset_index()
        tyredev.columns = ['Compound', 'TyreLife', 'LapTime', 'Count']


        fig, ax = plt.subplots(figsize=(10,6))
        for tyre,color in zip(['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'], ['red', 'yellow', 'white', 'green', 'blue']):
            df = tyredev[(tyredev['Compound'] == tyre)].dropna()
            if not df.empty:
                df.plot('TyreLife', 'LapTime', ax=ax, color=color, label=tyre, marker = 'o')
        if(drv != None):
            _ = ax.set_ylim((int(tyredev.LapTime.min()/10))*10, (int(tyredev.LapTime.max()/10)+1)*10)
        
        if(drv != None):
            _ = ax.set_title(f"{drv} Tyre degradation - {self.event.event['EventName']} {self.year}")
        else:
            _ = ax.set_title(f"Tyre degradation - {self.event.event['EventName']} {self.year}")
        _ = ax.set_ylabel('Fuel-Corrected Laptime (s)')

    def driver_laptimes(self, drv):
        driver_laps = self.event.laps.pick_driver(drv).pick_quicklaps().reset_index()

        nolaps = self.event.total_laps
        totfuel = 110
        secperkg = 0.03
        driver_laps['Fuel'] = totfuel - (driver_laps['LapNumber'] * (totfuel / nolaps))
        driver_laps['LapTime'] = driver_laps['LapTime'] / np.timedelta64(1, 's') - (secperkg * driver_laps['Fuel'])
        fig, ax = plt.subplots(figsize=(8, 8))

        sns.scatterplot(data=driver_laps,
                        x="LapNumber",
                        y="LapTime",
                        ax=ax,
                        hue="Compound",
                        palette=ff1.plotting.COMPOUND_COLORS,
                        s=80,
                        linewidth=0,
                        legend='auto')
        plt.xlabel("Laps")
        plt.ylabel("Fuel-Corrected Laptime")


    
    def engine_manufacter(self):
        
        list_fastest_laps = list()  
        for drv in self.event.results['Abbreviation']:
            drvs_fastest_lap = self.event.laps.pick_driver(drv).pick_fastest()
            if not pd.isna(drvs_fastest_lap['LapTime']):
                list_fastest_laps.append(drvs_fastest_lap)
        fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)
        driver_pole = fastest_laps.pick_fastest()
        lap_time_pole_string = strftimedelta( driver_pole['LapTime'], '%m:%s.%ms')
        plt.rcParams["figure.figsize"] = [12, 6]
        fig, ax = plt.subplots()

        f1_teams_engine = {      'Red Bull Racing': 'Red Bull Racing', 
                          'Ferrari': 'Ferrari',
                          'Haas F1 Team': 'Ferrari', 
                          'Aston Martin': 'Mercedes', 
                          'Alpine' : 'Alpine',
                          'Alfa Romeo': 'Ferrari',
                          'AlphaTauri': 'Red Bull Racing', 
                          'McLaren': 'Mercedes',
                          'Mercedes': 'Mercedes',
                          'Williams': 'Mercedes'}

        for drv in self.event.results['Abbreviation']:
                drv_fastest_lap = self.event.laps.pick_driver(drv).pick_fastest()
                if not pd.isna(drv_fastest_lap['LapTime']):
                    deltaTime = drv_fastest_lap['LapTime'] - driver_pole['LapTime'] 
                    color = ff1.plotting.team_color(f1_teams_engine[drv_fastest_lap['Team']])
                    ax.scatter(drv_fastest_lap.get_telemetry()['Speed'].max(), pd.Timedelta(deltaTime).total_seconds(), color = color)
                    ax.text(drv_fastest_lap.get_telemetry()['Speed'].max() + 0.1, pd.Timedelta(deltaTime).total_seconds() + 0.03, drv)
        ax.set(xlabel='Speed- Telem Max. (km/h)', ylabel= 'LapTime Delta(s)')
        plt.suptitle(f"LapTime by Engine Manufacturer\n{self.event.event['EventName']} {self.year} \n"
                        f"Fastest Lap: {lap_time_pole_string} ({driver_pole['Driver']})")
        plt.savefig('Engine', dpi=350)

    def tyre_strategy(self):
        fig, ax = plt.subplots(figsize=(12,8))

        pitstops = self.event.laps[['LapNumber', 'Stint', 'Driver']].copy()
        pitstops['Pitstop'] = ~pitstops.Stint.eq(pitstops.Stint.shift())
        pitstops = pitstops[pitstops.Pitstop] 
        pitstops = pitstops[pitstops.LapNumber > 1]
        pitstops.plot.scatter('LapNumber', 'Driver', ax=ax, color='purple', s=100)
        df = self.event.laps[['Driver', 'LapNumber', 'Compound']]
        df = pd.merge(self.event.results[['Abbreviation']], df, left_on='Abbreviation', right_on='Driver')
        for tyre,color in zip(['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'], ['red', 'yellow', 'white', 'green', 'blue']):
            df = self.event.laps[self.event.laps.Compound == tyre][['Driver', 'LapNumber', 'Compound']]
            df.plot.scatter('LapNumber', 'Driver', ax=ax, color=color, s=16)
        ax.invert_yaxis()
        ax.set_title(f"Tyre Strategy - {self.event.event['EventName']} {self.year}")
        plt.show()
    
    def circuit_info(self):
        return self.event.get_circuit_info()

    
    def race_trace_chart(self, drivers = [], inilap = None, nlaps = None):

        if(nlaps == None):
            nlaps = self.event.total_laps
        
        if(inilap == None):
            inilap = 1

        if(drivers == []):
            drivers = list(self.get_drivers())
        
        average_driver_laptime = []
        for driver in self.event.results['Abbreviation'][:10]:
            driver_laps = self.event.laps.pick_driver(driver)
            driver_laps['LapTimeSeconds'] = driver_laps['Time'].dt.total_seconds()
            average_driver_laptime.append(driver_laps['LapTimeSeconds'].reset_index(drop = True))
        virtual_driver = pd.DataFrame(average_driver_laptime)

        plt.rcParams["figure.figsize"] = [20, 10]
        plt.rcParams["figure.autolayout"] = True
        fig, ax = plt.subplots()
        color_list = []

        if(drivers == []):
            drivers = self.event.results['Abbreviation'] 
        
        for driver in drivers:
            driver_laps = self.event.laps.pick_driver(driver)
            driver_laps['LapTimeSeconds'] = driver_laps['Time'].dt.total_seconds()
            try:
                color = ff1.plotting.team_color(driver_laps['Team'].reset_index(drop=True)[0])
            except Exception as e:
                color = "#800080"
            if color in color_list:
                ax.plot(driver_laps['LapNumber'][inilap - 1:nlaps], virtual_driver.mean().reset_index(drop=True)[inilap - 1:len(driver_laps['LapTimeSeconds'][:nlaps])] - driver_laps['LapTimeSeconds'].reset_index(drop=True)[inilap - 1:nlaps], marker = 'o', label= driver, color = color, ls='--')
            else:
                ax.plot(driver_laps['LapNumber'][inilap - 1:nlaps], virtual_driver.mean().reset_index(drop=True)[inilap - 1:len(driver_laps['LapTimeSeconds'][:nlaps])] - driver_laps['LapTimeSeconds'].reset_index(drop=True)[inilap - 1:nlaps], marker = 'o', label= driver)
            color_list.append(color)

        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        ax.set(xlabel='Laps', ylabel= '<-- Driver behind // Driver ahead --> ')
        plt.title(f"Race Trace - {self.event.event['EventName']} {self.year}")
        plt.savefig(f"Race_Trace_{self.event.event['EventName']}", dpi=350)

    def plot_top_speed(self):
        drslist = []
        for driver in self.event.laps.Driver.unique():
            drs = self.event.laps.pick_driver(driver).get_telemetry()[['Speed', 'DRS']].groupby('DRS').max()
            withoutDRS = drs[drs.index < 5]['Speed'].max()
            withDRS = drs[drs.index > 5]['Speed'].max()
            drslist.append({'Driver':driver, 'DRS':withDRS, 'noDRS': withoutDRS})
        topspeeds = pd.DataFrame(drslist)

        fig, ax = plt.subplots(figsize=(15,10))
        topspeeds.plot.scatter('Driver', 'DRS', ax=ax, color='orange', s=16, label='DRS')
        topspeeds.plot.scatter('Driver', 'noDRS', ax=ax, color='lightskyblue', s=16, label='no DRS')
        ax.axhline(topspeeds.DRS.mean(), color='orange' )
        ax.axhline(topspeeds.noDRS.mean(), color='lightskyblue', linestyle = '--')
        ax.set_title('Top Speed')
        ax.legend()
        plt.show()
    
    
    def plot_bargraph_team(self, session = 'q3'):
        
        q1, q2 , q3 = self.event.laps.split_qualifying_sessions()
        if(session == 'q1'):
            best_team_laptimes = q1.groupby('Team')['LapTime'].min().reset_index()
        elif(session == 'q2'):
            best_team_laptimes = q2.groupby('Team')['LapTime'].min().reset_index()
        else:
            best_team_laptimes = q3.groupby('Team')['LapTime'].min().reset_index()
        
        best_team_laptimes['LapTime'] = pd.to_timedelta(best_team_laptimes['LapTime'] - best_team_laptimes['LapTime'].min()).dt.total_seconds()
        plt.figure(figsize=(12, 6.75))
        sns.barplot(x='LapTime', y='Team', data=best_team_laptimes.sort_values(by='LapTime', ascending= True),  palette=[ff1.plotting.team_color(team) for team in best_team_laptimes.sort_values(by='LapTime', ascending= True)['Team']])
        plt.grid(axis='both', linestyle='--', alpha=0.7)
        plt.show()

    
    def plot_car_characteristics(self):
        laps = self.event.laps
        min_lap_indexes = laps.groupby('Team')['LapTime'].idxmin()
        drivers_with_fastest_lap = laps.loc[min_lap_indexes, ['Driver', 'LapTime', 'Team']]
        df = drivers_with_fastest_lap.sort_values(by='LapTime')
        high_speed = []
        plt.rcParams["figure.figsize"] = [12, 6]
        fig, ax = plt.subplots()
        for drv in df['Driver']:
            color = ff1.plotting.team_color(laps.pick_driver(drv)['Team'].reset_index(drop = True)[0])
            telemetry = laps.pick_driver(drv).pick_fastest().get_telemetry()
            high_speed.append((telemetry['Speed'].mean(),color, telemetry['Speed'].max(), laps.pick_driver(drv)['Team'].reset_index(drop = True)[0]))

        ax.set(xlabel='Mean Speed (km/h)', ylabel= 'Top Speed (km/h)')
        plt.scatter(list(zip(*high_speed))[0],list(zip(*high_speed))[2], color = list(zip(*high_speed))[1])

        for i in range(len(high_speed)):
            ax.annotate(list(zip(*high_speed))[3][i], (list(zip(*high_speed))[0][i], list(zip(*high_speed))[2][i] + 0.3))

        plt.suptitle(f"Car Characteristics\n{self.event.event['EventName']} {self.year} - {race_type_enum[self.modality]}")
        plt.savefig('car_characteristics', dpi=350)
    
    def position_changes(self):
        fig, ax = plt.subplots(figsize=(12, 6))
        for drv in  list(np.unique(self.get_laps_race()['Driver'])):
            drv_laps = self.event.laps.pick_driver(drv)

            abb = drv_laps['Driver'].iloc[0]
            if(abb == 'LAW' or abb == 'RIC'):
                color = ff1.plotting.driver_color('DEV')
            else:
                color = ff1.plotting.driver_color(abb)

            ax.plot(drv_laps['LapNumber'], drv_laps['Position'],
                    label=abb, color=color)
        ax.set_ylim([20.5, 0.5])
        ax.set_yticks([1, 5, 10, 15, 20])
        ax.set_xlabel('Lap')
        ax.set_ylabel('Position')
        ax.legend(bbox_to_anchor=(1.0, 1.02))
        plt.title(f"Race Positions - {self.event.event['EventName']} {self.year}")
        plt.tight_layout()

    def session_pace_evolution(self):
        q1, q2, q3 = self.event.laps.split_qualifying_sessions()
        fig, ax = plt.subplots()
        resultados_q1 = q1.groupby('Team')['LapTime'].min().reset_index().sort_values(by='LapTime', ascending=True)
        resultados_q2 = q2.groupby('Team')['LapTime'].min().reset_index().sort_values(by='LapTime', ascending=True)
        resultados_q3 = q3.groupby('Team')['LapTime'].min().reset_index().sort_values(by='LapTime', ascending=True)

        resultados_q1['Qualify'] = 'Q1'
        resultados_q2['Qualify'] = 'Q2'
        resultados_q3['Qualify'] = 'Q3'

        resultados_totais = pd.concat([resultados_q1, resultados_q2, resultados_q3])
        resultados_totais['LapTimeSeconds'] = resultados_totais['LapTime'].dt.total_seconds()


        # Crie um gráfico de linha para cada equipe
        for team in resultados_totais['Team'].unique():
            team_data = resultados_totais[resultados_totais['Team'] == team]
            ax.plot(team_data['Qualify'], team_data['LapTimeSeconds'], label=team, marker='o', color=ff1.plotting.team_color(team))
        
        ax.set(xlabel='Qualify', ylabel= 'LapTime (seconds)')
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        plt.suptitle(f"{self.event.event['EventName']} {self.year} \n"
                        f"Session Pace Evolution")