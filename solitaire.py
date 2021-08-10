import re
from game_elements import Game
import operator
from itertools import permutations  
from collections import OrderedDict

import pandas as pd 
import math

class Strategy:
	def __init__(self,rule_order,col_order,verbose=False):
		self.col_order = col_order
		self.rule_order = rule_order
		self.verbose=verbose
		self.rule_dict = {1: self.moveTableauToFoundation, 
					2: self.moveWasteToFoundation, 
					3: self.fillOpenWithKings,
					4: self.addWasteToTableau,
					5: self.moveCardsToExpose}

	def setGame(self,game):
		self.game=game

	def orderedRuleDict(self):
		ordered_rules = OrderedDict.fromkeys(self.rule_order)
		for key in ordered_rules:
			ordered_rules[key]=self.rule_dict[key]

		return ordered_rules					

	def moveTableauToFoundation(self):
		#Check if can move any Tableau Cards to Foundation
		for col_index in self.col_order:
			column_cards = self.game.t.flipped[col_index]			
			if len(column_cards)>0:
				command = f"tf{col_index+1}"
				if self.game.takeTurn(command):
					if self.verbose:
						print(command)
					return True	
		return False

	def moveWasteToFoundation(self):
		# Check if I can move any Waste to Foundation
		if self.game.takeTurn("wf"):
			if self.verbose:
				print("wf")
			return True	
	
		return False

	def fillOpenWithKings(self):
		# If there is an open tableau, move king to it:
		for col_index in self.col_order:
			if len(self.game.t.flipped[col_index])==0:
				#Check if we can move from any Tableau to Foundation
				for col_index2 in self.col_order: 
					if col_index != col_index2:
						# Only move King if its part of a pile with Unexposed cards (Don't want to move king from one blank pile to other)
						if len(self.game.t.flipped[col_index2]) > 0 and len(self.game.t.unflipped[col_index2])>0 and self.game.t.flipped[col_index2][0].value == 13:
							command = f"tt{col_index2+1}{col_index+1}"
							if self.game.takeTurn(command):
								if self.verbose:
									print(command)
								return True


				#Check if we can move any king from waste to tableau
				if self.game.sw.getWaste()!="empty":
					if self.game.takeTurn(f"wt{col_index+1}"):
						if self.verbose:
							print(f"wt{col_index+1}")	
						return True 

		return False

	def addWasteToTableau(self):
		# Add Waste Cards to Tableau
		for col_index in self.col_order:
			column_cards = self.game.t.flipped[col_index]			
			if len(column_cards)>0:
				# Make sure Waste is not Empty
				if self.game.sw.getWaste()!="empty":    
					if self.game.takeTurn(f"wt{col_index+1}"):
						if self.verbose:
							print(f"wt{col_index+1}")
						return True
		return False

	def moveCardsToExpose(self):

		# Only Move Cards from Pile 1 to Pile 2 if Can Expose New Cards
		for p1_index in self.col_order:			
			if len(self.game.t.flipped[p1_index])>0:
				for p2_index in self.col_order:
					if p1_index != p2_index and len(self.game.t.flipped[p2_index])>0:
						# Move only if the last card in Pile 2 Flipped can be attached to first card for Pile 1 Fixed
						if self.game.t.flipped[p2_index][-1].canAttach(self.game.t.flipped[p1_index][0]):
							command = f"tt{p1_index+1}{p2_index+1}"
							if self.game.takeTurn(command):
									if self.verbose:
										print(command)	
									return True
		return False






class Simulation:
	def __init__(self,output_log,num_runs=100,max_turns=100,verbose=False):
		self.output_log=output_log
		self.verbose = verbose
		self.num_runs=num_runs
		self.max_turns=max_turns
		

		with open(self.output_log,"w") as a_file:
			new_line = "score,num_moves,game_duration,did_win"
			a_file.write(new_line)


	def simulateRulePerm(self,strategy):
		self.num_turns +=1

		#Always make sure 1 card from the deck is visible
		if self.game.sw.getWaste() == "empty":
			if self.game.takeTurn("mv"):
				if self.verbose:
					print("mv")
				return True

		rule_dict = strategy.orderedRuleDict()
	
		for rule in rule_dict:
			if rule_dict[rule]():
				return True

		return False

	def basicAuto(self, strategy):
		if self.game.gameWon():
			return False

		turnResult = self.simulateRulePerm(strategy)
		if self.verbose:
			self.game.printTable()

		if turnResult:
			self.basicAuto(strategy)

		else: 
			if self.num_turns < self.max_turns:
				#End draw from deck 
				self.game.takeTurn("mv")
				return self.basicAuto(strategy)




	def runManual(self):
		self.game = Game(verbose=self.verbose)
		self.game.printValidCommands()
		self.game.printTable()

		while not self.game.gameWon():
			command = input("Enter a command (type 'h' for help): ")
			command = command.lower().replace(" ", "")
			if command == "h":
				self.game.printValidCommands()
			elif command == "q":
				print("Game exited.")
				break
			elif re.match("|".join(['mv','wf','wt','tf','tt']), command):
				self.game.takeTurn(command)
				self.game.printTable()
			else:
				print("Sorry, that is not a valid command.")


		if self.game.gameWon():
			print("Congratulations! You've won!")

		score,num_moves, game_duration, did_win = self.game.getFinalMetrics()
		print(f"Final Score: {score} \nNum Moves: {num_moves} \nGame Duration: {game_duration} seconds")
		
		self.outputToLog()

	def outputToLog(self):
		score,num_moves, game_duration, did_win = self.game.getFinalMetrics()
		new_line = f"{score},{num_moves},{game_duration},{did_win}"
		with open(self.output_log,"a") as a_file:
			a_file.write("\n")
			a_file.write(new_line)

	def runAuto(self,strategy):
		for i in range(self.num_runs):
			# For Each Run, Create a New Game and Reset Numb Terms
			self.num_turns=0
			self.game = Game(verbose=self.verbose)
			strategy.setGame(self.game)

			self.basicAuto(strategy)
			self.outputToLog()


if __name__ == "__main__":
	# ------------- Play Solitaire Manually in the Interactive Command Prompt ---------------------------------------------- #
	simulation = Simulation('runs_manual.log',verbose=True)
	simulation.runManual()

	# ------------- Run Automatic Solitaire Simulations based on Parameters ------------------------------------------------ #
	## Specify Rule Order
	rule_order=list(range(1,6))
	## Specify Column Order
	col_order=list(range(7))
	## Specify Number of Simulation Iterations
	num_runs = 1000 
	## Specify Number of Max Turns per Round (To prevent infinite looping)
	max_turns = 300 	

	# Create a Simulation Object with Run Parameters
	simulation = Simulation('logs/runs_auto_basic_{num_run}_{max_turns}_{rule_order}_{col_order}.log',num_runs=num_runs,max_turns=max_turns)

	# Create a Strategy Object that specifies Rule Order and Column Order
	strategy = Strategy(rule_order=rule_order,col_order=col_order,verbose=simulation.verbose)

	# Run the Simulation
	simulation.runAuto(strategy)

	# ------------------- Advanced Calcualtions for Benchmarking Below, Feel Free to Ignore ------------------------------#

	# num_runs=500
	# num_turns=300
	
	# with open(f"logs/summary_{num_runs}_{num_turns}.csv","w") as a_file:
	# 	a_file.write("log_file,num_runs,num_turns,rule_order,col_order,avg_win_rate,avg_moves_win,ci95_win_rate")


	# rule_perm = list(permutations(list(range(1,6))))
	# col_perm = list(permutations(list(range(7))))	



	# col_order=list(range(6,-1,-1))
	# for rule_order in rule_perm:
	# 	rule_order_str = ''.join("{0}".format(n) for n in rule_order)
	# 	col_order_str = ''.join("{0}".format(n) for n in col_order)
	# 	output_log_name = f'logs/runs_auto_basic_{num_runs}_{num_turns}_{rule_order_str}_{col_order_str}.log'
		
	# 	simulation = Simulation(output_log_name,num_runs=num_runs,max_turns=num_turns)

	# 	# Create a Strategy Object that specifies Rule Order and Column Order
	# 	strategy = Strategy(rule_order=rule_order,col_order=col_order,verbose=simulation.verbose)

	# 	simulation.runAuto(strategy)			

		

	# 	log_pd = pd.read_csv(output_log_name)

	# 	avg_win_rate = log_pd.did_win.mean()

	# 	avg_moves_win = log_pd[log_pd.did_win==1].num_moves.mean()

	# 	ci95_win_rate = 1.96*math.sqrt(avg_win_rate*(1-avg_win_rate)/1000)

	# 	new_line=f"{output_log_name},{num_runs},{num_turns},{rule_order_str},{col_order_str},{avg_win_rate},{avg_moves_win},{ci95_win_rate}"


	# 	with open(f"logs/summary_{num_runs}_{num_turns}.csv","a") as a_file:
	# 		a_file.write("\n")

	# 		a_file.write(new_line)


	# num_turns = 300
	# rule_order=range(5,0,-1)
	# col_order=list(range(6,-1,-1))
	# rule_order_str = ''.join("{0}".format(n) for n in rule_order)
	# col_order_str = ''.join("{0}".format(n) for n in col_order)

	# summary_file_name = f"logs/summary_{num_turns}_{rule_order_str}_{col_order_str}.csv"
	# with open(summary_file_name,"w") as a_file:
	# 	a_file.write("log_file,num_runs,num_turns,rule_order,col_order,avg_win_rate,avg_moves_win,ci95_win_rate")

	# for num_runs in range(100,1000,100):

	# 	output_log_name = f'logs/runs_auto_basic_{num_runs}_{num_turns}_{rule_order_str}_{col_order_str}.log'
		
	# 	simulation = Simulation(output_log_name,num_runs=num_runs,max_turns=num_turns)

	# 	# Create a Strategy Object that specifies Rule Order and Column Order
	# 	strategy = Strategy(rule_order=rule_order,col_order=col_order,verbose=simulation.verbose)

	# 	simulation.runAuto(strategy)			

	# 	log_pd = pd.read_csv(output_log_name)

	# 	avg_win_rate = log_pd.did_win.mean()

	# 	avg_moves_win = log_pd[log_pd.did_win==1].num_moves.mean()

	# 	ci95_win_rate = 1.96*math.sqrt(avg_win_rate*(1-avg_win_rate)/1000)

	# 	new_line=f"{output_log_name},{num_runs},{num_turns},{rule_order_str},{col_order_str},{avg_win_rate},{avg_moves_win},{ci95_win_rate}"


	# 	with open(summary_file_name,"a") as a_file:
	# 		a_file.write("\n")

	# 		a_file.write(new_line)