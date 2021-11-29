import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
from collections import deque
import heapq
import math
import csv
import os

POPULATION_SIZE = 20
EVALUATION_NUMBER = 2

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

	#instance variables


	#__init__
	#Description: Creates a new Player
	#
	#Parameters:
	#   inputPlayerId - The id to give the new player (int)
	#   cpy           - whether the player is a copy (when playing itself)
	##
	def __init__(self, inputPlayerId):
		super(AIPlayer,self).__init__(inputPlayerId, "RodgerRises")
		self.population = []
		self.popIndex = 0
		self.evalIndex = 0
		self.fitni = []
		self.initPopulation()


	def initPopulation(self):
		if(os.path.exists('mcmo_population.csv')):
			freshStart = False
		else:
			freshStart = True
		print("Fresh Start", freshStart)
		if freshStart:
			for gene in range(POPULATION_SIZE):
				gene = []
				for i in range(12):
					gene.append(random.uniform(-10.0,10.0))
				self.population.append(gene)
				self.fitni.append(0)
		else:
			for i in range(POPULATION_SIZE):
				self.fitni.append(0)
			with open('mcmo_population.csv', 'r', newline = '') as f:
				reader = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)
				self.population = list(reader)

				


	def createChildren(self, parent1, parent2):
		split = random.randint(1,11)
		frontHalf = slice(0, split)
		backHalf = slice(split, 12)

		# print(parent1, "   ", parent2)

		child1 = parent1[frontHalf] + parent2[backHalf]
		child2 = parent2[frontHalf] + parent1[backHalf]

		if(random.randint(1, 100) <= 5):
			if(random.randint(1,2) == 1):
				child1 = self.mutate(child1)
			else:
				child2 = self.mutate(child2)

		# print(child1, "   ", child2)

		return [child1, child2]
	
	def mutate(self, child):
		if(random.randint(0,1) == 0):
			for value in child:
				value = value * -1
		else:
			print(child, "\n")
			temp = deque(child)
			temp.rotate(random.randint(1,11))
			child = list(temp)
			print(child)

		return child

	def createNextGeneration(self):
		newPopulation = []
		sortedPopulation = [x for _,x in sorted(zip(self.fitni, self.population))]
		for i in range(int(POPULATION_SIZE/4)):
			newChildren = self.createChildren(sortedPopulation[i], sortedPopulation[int(POPULATION_SIZE/2-1-i)])
			newPopulation.append(newChildren[0])
			newPopulation.append(newChildren[1])
			newChildren = self.createChildren(sortedPopulation[i], sortedPopulation[i + 1])
			newPopulation.append(newChildren[0])
			newPopulation.append(newChildren[1])
			
		self.population = newPopulation
		#Save population
		with open('./AI/mcmo_population.csv', 'w', newline='') as file:
			mywriter = csv.writer(file, delimiter=',')
			mywriter.writerows(self.population)


	def averageDist(self, group1, group2):
		distSum = 0
		divisor = 0
		if(isinstance(group1, list)):
			for unit1 in group1:
				if(isinstance(group2, list)):
					for unit2 in group2:
						distSum += approxDist(unit1.coords, unit2.coords)
						divisor += 1
				else:
					distSum += approxDist(unit1.coords, group2.coords)
					divisor += 1
		else:
			if(isinstance(group2, list)):
				for unit2 in group2:
					distSum += approxDist(group1.coords, unit2.coords)
					divisor += 1
			else:
				distSum += approxDist(group1.coords, group2.coords)
				divisor += 1
		averageSum = distSum
		if(divisor != 0):
			averageSum = averageSum/divisor
		return averageSum

	#utility
	#
	#Parameters:
	#   currentState - the current game state
	#   move - the move to get to the current game state
	#
	#Returns the utility of the given state
	#Notes: score is not optimisticc to avoid negative scores which cause bad behavior
	def utility(self, currentState, move, playerID):
		value = 0
		i = self.popIndex

		myInv = getCurrPlayerInventory(currentState)

		if myInv.player == 0:
			enemyInv = currentState.inventories[1]
		else:
			enemyInv = currentState.inventories[0]
		
		# Get important pieces.
		myFood = myInv.foodCount
		myFoodPlacement = getCurrPlayerFood(self, currentState)
		enemyFood = enemyInv.foodCount
		myAnts = myInv.ants
		enemyAnts = enemyInv.ants
		myCombatAnts = getAntList(currentState, myInv.player, (DRONE, SOLDIER, R_SOLDIER))
		enemyCombatAnts = getAntList(currentState, enemyInv.player, (DRONE, SOLDIER, R_SOLDIER))
		myWorkerAnts = getAntList(currentState, myInv.player, (WORKER,))
		enemyWorkerAnts = getAntList(currentState, enemyInv.player, (WORKER,))
		myQueen = myInv.getQueen()
		enemyQueen = enemyInv.getQueen()
		myAnthill = myInv.getAnthill()
		myTunnel = myInv.getTunnels()[0]
		enemyAnthill = enemyInv.getAnthill()		
		
		value += (self.population[i][0] * 
			(myFood - enemyFood))
		value += (self.population[i][1] * 
			(myInv.getQueen().health - enemyInv.getQueen().health))
		value += (self.population[i][2] *
			self.averageDist(enemyQueen, myCombatAnts))
		value += (self.population[i][3] *
			self.averageDist(enemyCombatAnts, myQueen))
		value += (self.population[i][4] *
			self.averageDist(enemyAnthill, myCombatAnts))
		value += (self.population[i][5] *
			self.averageDist(enemyCombatAnts, myAnthill))
		value += (self.population[i][6] *
			self.averageDist(myWorkerAnts, myFoodPlacement))
		value += (self.population[i][7] *
			(len(myCombatAnts) - len(enemyCombatAnts)))
		value += (self.population[i][8] * 
			(myAnthill.captureHealth - enemyAnthill.captureHealth))
		value += (self.population[i][9] *
			self.averageDist(myCombatAnts, enemyWorkerAnts))
		value += (self.population[i][10] *
			approxDist(myQueen.coords, enemyQueen.coords))
		value += (self.population[i][11] * 
			self.averageDist(myTunnel, enemyWorkerAnts))

		return value

	##
	#getPlacement
	#
	#Description: called during setup phase for each Construction that
	#   must be placed by the player.  These items are: 1 Anthill on
	#   the player's side; 1 tunnel on player's side; 9 grass on the
	#   player's side; and 2 food on the enemy's side.
	#
	#Parameters:
	#   construction - the Construction to be placed.
	#   currentState - the state of the game at this point in time.
	#
	#Return: The coordinates of where the construction is to be placed
	##
	def getPlacement(self, currentState):
		numToPlace = 0
		#implemented by students to return their next move
		if currentState.phase == SETUP_PHASE_1:    #stuff on my side
			numToPlace = 11
			moves = []
			for i in range(0, numToPlace):
				move = None
				while move == None:
					#Choose any x location
					x = random.randint(0, 9)
					#Choose any y location on your side of the board
					y = random.randint(0, 3)
					#Set the move if this space is empty
					if currentState.board[x][y].constr == None and (x, y) not in moves:
						move = (x, y)
						#Just need to make the space non-empty. So I threw whatever I felt like in there.
						currentState.board[x][y].constr == True
				moves.append(move)
			return moves
		elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
			numToPlace = 2
			moves = []
			for i in range(0, numToPlace):
				move = None
				while move == None:
					#Choose any x location
					x = random.randint(0, 9)
					#Choose any y location on enemy side of the board
					y = random.randint(6, 9)
					#Set the move if this space is empty
					if currentState.board[x][y].constr == None and (x, y) not in moves:
						move = (x, y)
						#Just need to make the space non-empty. So I threw whatever I felt like in there.
						currentState.board[x][y].constr == True
				moves.append(move)
			return moves
		else:
			return [(0, 0)]

	##
	#expandNode
	#
	#Description: expands a node and discovers adjacent nodes
	#
	#Parameters:
	#node: the node to be expanded
	#
	#Returns a list of adjacent nodes
	def expandNode(self, node, myID):
		#gets all legal moves from a state
		allMoves = listAllLegalMoves(node["state"])
		nodeList = []
		#goes through every move and makes a new node
		for move in allMoves:
			moveState = getNextStateAdversarial(node["state"], move)
			if move.moveType != END:
				nodeDict = {
					"move": move,
					"state": moveState,
					"depth": node["depth"] + 1,
					"evaluation": self.utility(moveState, move, myID),
					"parent": node,
					"max_not_min":node["max_not_min"],
					"max": None,
					"min": None
				}
			else:
				nodeDict = {
					"move": move,
					"state": moveState,
					"depth": node["depth"] + 1,
					"evaluation": self.utility(moveState, move, myID),
					"parent": node,
					"max_not_min":not node["max_not_min"],
					"bestMove": None,
					"max": None,
					"min": None
				}
			if nodeDict["depth"] > 2:
				continue
			nodeList.append(nodeDict)
		sorted_node_list = sorted(nodeList, key = lambda node:node["evaluation"], reverse=False)
		return sorted_node_list[0: math.ceil(0.1 * len(nodeList))]
		
	##
	#getBestMove
	#
	#Description: uses minmax to get the best move
	#
	#Parameters: 
	#rootNode: the node to get the best move for
	#myID: id of the player who needs the best move
	def getBestMove(self, rootNode, myID):
		#gets all the possible moves from a state
		possible_moves = self.expandNode(rootNode, myID)
		#base case is when there are no moves
		if possible_moves == []:
				return rootNode["evaluation"]
		#goes through each move
		for node in possible_moves:
				
				best_move_utility = self.getBestMove(node, myID)
				
				#if theres no min yet, makes one
				if rootNode["max_not_min"] and rootNode['min'] == None:
					rootNode["min"] = best_move_utility
					rootNode["bestMove"] = node["move"]
				#if utility is a better min, saves it
				elif rootNode["max_not_min"] and best_move_utility < rootNode['min']:
					rootNode["min"] = best_move_utility
					rootNode["bestMove"] = node["move"]
				#if theres no max yet, makes one
				elif not rootNode["max_not_min"] and rootNode['max'] == None:
					rootNode["max"] = best_move_utility
					rootNode["bestMove"] = node["move"]
				#if utility is a better max, saves it
				if not rootNode["max_not_min"] and best_move_utility > rootNode['max']:
					rootNode["max"] = best_move_utility
					rootNode["bestMove"] = node["move"]
				#alpha beta pruning if possible
				if rootNode["parent"] != None:
					if rootNode["max_not_min"] and not rootNode["parent"]["max_not_min"] and rootNode["parent"]["max"] != None and rootNode["min"] < rootNode["parent"]["max"]:
						return rootNode["min"]
					elif not rootNode["max_not_min"] and rootNode["parent"]["max_not_min"] and rootNode["parent"]["max"] != None and rootNode["max"] > rootNode["parent"]["min"]:
						return rootNode["max"]
		
		#returns the proper min or max move
		if rootNode["max_not_min"]:
			return rootNode["min"]
		else:
			return rootNode["max"]

	#method used just for testing
	def printNode(self, node):
		if (node["max_not_min"]):
			if node["min"] == None:
				print("Weird min evaluation" + str(node["evaluation"]) + " Move: " + str(node["move"]))
				return
			print("MAX Evaluation: " + str(node["min"]) + " Move: " + str(node["bestMove"]))
		else:
			if node["max"] == None:
				print("Weird max evaluation" + str(node["evaluation"]) + " Move: " + str(node["move"]))
				return
			print("MIN Evaluation: " + str(node["max"]) + " Move: " + str(node["bestMove"]))

		

	##
	#getMove
	#Description: Gets the next move from the Player.
	#
	#Parameters:
	#   currentState - The state of the current game waiting for the player's move (GameState)
	#
	#Return: The Move to be made
	##
	def getMove(self, currentState):
		myID = currentState.whoseTurn

		#creates a base node
		rootNode = {
			"move": None,
			"state": currentState,
			"depth": 0,
			"evaluation": self.utility(currentState, None, myID),
			"parent": None,
			"max_not_min": True,
			"max": None,
			"min": None
		}
		
		best_node = self.getBestMove(rootNode, myID)
		return rootNode["bestMove"]


	##
	#getAttack
	#Description: Gets the attack to be made from the Player
	#
	#Parameters:
	#   currentState - A clone of the current state (GameState)
	#   attackingAnt - The ant currently making the attack (Ant)
	#   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
	##
	def getAttack(self, currentState, attackingAnt, enemyLocations):
		#Attack a random enemy.
		return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

	##
	#registerWin
	#
	#Description: updates the fitness of the gene that just played and then either continues
	#				testing with current genes or generates a new population to test with
	#
	#Parameters:
	#	hasWon - whether or not the agent won
	def registerWin(self, hasWon):
		print("popIndex", self.popIndex)
		#has current gene been fully evaluated?
		if self.evalIndex == EVALUATION_NUMBER-1:
			print(self.fitni[self.popIndex])
			self.evalIndex = 0
			self.popIndex += 1
		else:
			self.evalIndex += 1
		#we are finished with this population so we generate new population
		if self.popIndex == POPULATION_SIZE:
			self.evalIndex = 0
			self.popIndex = 0
			self.createNextGeneration()
			
		else:
			if(self.fitni[self.popIndex] == None):
				self.fitni[self.popIndex] = (hasWon * 100) / EVALUATION_NUMBER
			else:
				self.fitni[self.popIndex] += (hasWon * 100) / EVALUATION_NUMBER
		