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

ALPHA_VALUE = .1
DISCOUNT_VALUE = .8
FILENAME = "morganco23states.txt"

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

	#__init__
	#Description: Creates a new Player
	#
	#Parameters:
	#   inputPlayerId - The id to give the new player (int)
	##
	def __init__(self, inputPlayerId):
		super(AIPlayer,self).__init__(inputPlayerId, "TDLEARNER")
		self.states = {}
		self.currentState = None
		self.nextState = None
		self.initPopulation()

	#initPopulation
	#Description: initializes our local statespace from
	#				the save file
	#
	#Parameters:
	#	self
	def initPopulation(self):
		self.states = {}
		with open('../'+FILENAME, 'r', newline = '') as f:
			reader = csv.reader(f)
			for val in reader:
				for entry in val:
					red = entry.split(': ')
					if(len(red) == 2):
						state = red[0]
						value = red[1]

						self.states[state] = float(value)
		f.close()
				

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
	#getMove
	#Description: Gets the next move from the Player.
	#
	#Parameters:
	#   currentState - The state of the current game waiting for the player's move (GameState)
	#
	#Return: The Move to be made
	##
	def getMove(self, currentState):
		#get next possible moves and then choose a random one
		allmoves = listAllLegalMoves(currentState)
		mymove = allmoves[random.randint(0,len(allmoves) - 1)]

		#TODO: add explore vs Exploit
		#currently exploiting
		for move in allmoves:
			if self.states.get(self.decideCategory(getNextStateAdversarial(currentState, mymove))) == None:
				continue
			elif self.states.get(self.decideCategory(getNextStateAdversarial(currentState, move))) == None:
				continue
			elif self.states[self.decideCategory(getNextStateAdversarial(currentState, mymove))] < self.states[self.decideCategory(getNextStateAdversarial(currentState, move))]:
				mymove = move


		#don't want ants if we already have 1
		numWorkers = len(getAntList(currentState,currentState.whoseTurn,(WORKER,)))
		while numWorkers > 1 and mymove.moveType == BUILD:
			mymove = allmoves[random.randint(0,len(allmoves) - 1)]
		self.nextState = getNextStateAdversarial(currentState,mymove)

		self.currentState = currentState

		self.updateStateSpace(-.1, currentState, self.nextState)

		return mymove


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
		#win is 10, rest is -.1
		reward = -.1
		if hasWon:
			reward = 10
		
		#we need to update our statespace now
		self.updateStateSpace(reward, self.currentState, self.nextState)
		#we save after every game to not lose progress
		self.save()
	

	def updateStateSpace(self,reward,thiState, nextState):
		thisCategory = self.decideCategory(thiState)
		thisUtility = self.states.setdefault(thisCategory, 0)
		nextCategory = self.decideCategory(nextState)
		nextUtility = self.states.setdefault(nextCategory,0)

		newVal = thisUtility + ALPHA_VALUE*(reward + (DISCOUNT_VALUE * (nextUtility - thisUtility)))

		self.states[thisCategory] = newVal


	def decideCategory(self, state):
		#will return a category that will 
		#be a # separated list of of the category values

		#the different categories will be:
		#	- the number of workers
		#	- the food
		#	- the distance from food/tunnel of each ant

		myinv = getCurrPlayerInventory(state)
		myWorkers = getAntList(state, state.whoseTurn, (WORKER,))
		numWorkers = len(myWorkers)

		category = "" + str(numWorkers) + "#"
		category += "" + str(myinv.foodCount)

		myTunnel = getConstrList(state, state.whoseTurn, (TUNNEL,))[0]
		foods = getConstrList(state, None, (FOOD,))
		if numWorkers > 0:
			for worker in myWorkers:
				dist = 1000
				if worker.carrying:
					#dist from tunnel
					dist = approxDist(worker.coords, myTunnel.coords)


				else:
					#dist from food
					for food in foods:
						d = approxDist(worker.coords, food.coords)
						if d < dist:
							dist = d

				category += "#" + str(dist)
		return category



	def save(self):
		f = open(FILENAME, "w")
		towrite = ""
		for cat, val in self.states.items():
			towrite += "" + cat + ": " + str(val) + ", "
		f.write(towrite)
		f.close()