# -*- coding: utf-8 -*-
'''
Created on 2015-10-19 
@author: 陈逸逵 
'''
import math
import random
import cPickle as pickle
from os import path
import xlrd
import time

#calculate the overall average
def Average(trainData):
	result = 0.0
	cnt = 0
	for row in trainData:
		cnt += 1
		result += row[2]
	return result / cnt


def InerProduct(v1, v2):
	result = 0
	for i in range(len(v1)):
		result += v1[i] * v2[i]
		
	return result


def PredictScore(av, bu, bi, pu, qi,btcj,contextCondition):
	pScore = av + bu + bi + InerProduct(pu, qi)
        for key,value in btcj.iteritems():
                if contextCondition[key]>=0:
                        pScore+=value[int(contextCondition[key])]
	if pScore < 1:
		pScore = 1
	elif pScore > 5:
		pScore = 5
	return pScore
	
def MAE(testData,av,bu,bi,pu,qi,btcj,contextCondition):
        global userIdDict
        global itemIdDict
        global categoryIdDict
        cnt=0
        mae=0.0
	for arr in testData:
		cnt += 1
		uid = userIdDict[arr[0]]
		iid = itemIdDict[arr[1]]
                cid = categoryIdDict[arr[23]]
                contextCondition = list()
                for i in range(7,19):
                    contextCondition.append(arr[i]-1)
		pScore = PredictScore(av, bu[uid], bi[iid], pu[uid], qi[iid],btcj[cid],contextCondition)
			
		tScore = int(arr[2])
		mae += abs(tScore - pScore)
	fi.close()
        return mae/cnt

	
def CAMF_CC(configureFile,trainData,testData):
        global userIdDict
        global itemIdDict
        global categoryIdDict
        global userNum 
        global itemNum 
        global factorNum 
        global learnRate 
        global regularization 
        global categoryNum 

	averageScore = Average(trainData) 
        bu = [0.0 for i in range(userNum)]
        bi = [0.0 for i in range(itemNum)]
        temp = math.sqrt(factorNum)
        qi = [[(0.1 * random.random() / temp) for j in range(factorNum)] for i in range(itemNum)]	
        pu = [[(0.1 * random.random() / temp) for j in range(factorNum)] for i in range(userNum)]
	btcj = list()
	for i in range(categoryNum):
		contextDict = dict()
		for j in range(len(contextNum)):
			contextDict[j]=[0.0 for z in range(contextNum[j])]
	        btcj.append(contextDict)

        
        preMAE = 10000.0 
	for step in range(100):
		for arr in trainData:
		        uid = userIdDict[arr[0]]
		        iid = itemIdDict[arr[1]]
                        cid = categoryIdDict[arr[23]]
			score = int(arr[2])			

                        contextCondition = list()
                        for i in range(7,19):
                            contextCondition.append(int(arr[i])-1)
			prediction = PredictScore(averageScore, bu[uid], bi[iid], pu[uid], qi[iid],btcj[cid],contextCondition)
				
			eui = score - prediction
		
			#update parameters
			bu[uid] += learnRate * (eui - regularization * bu[uid])
			bi[iid] += learnRate * (eui - regularization * bi[iid])	

                        for key,values in btcj[cid].iteritems():
                                    value = values[contextCondition[key]]
                                    value += learnRate * (eui - regularization*value)
                                    btcj[cid][key][contextCondition[key]]=value

			for k in range(factorNum):
				temp = pu[uid][k]	#attention here, must save the value of pu before updating
				pu[uid][k] += learnRate * (eui * qi[iid][k] - regularization * pu[uid][k])
				qi[iid][k] += learnRate * (eui * temp - regularization * qi[iid][k])
		fi.close()
		curMAE = MAE(testData,averageScore, bu, bi, pu, qi,btcj,contextCondition)
		print("test_MAE in step %d: %f" %(step, curMAE))
		if curMAE >= preMAE:
			break
		else:
			preMAE = curMAE
					
	print("model generation over")
        return curMAE
	
def TenFloadValidate(data):
        mae = 0.0
        random.shuffle(data)
        flodLen = len(data)/10
        flodData = list()
        for i in range(10):
            flodData.append(data[flodLen*i:flodLen*(i+1)])


        for i in range(10):
            print 'flod in step %d starting...' %(i+1)
            testData=flodData[i]
            trainData=list()
            for j in range(i):
                trainData.extend(flodData[j])
            for j in range(i+1,10):
                trainData.extend(flodData[j])

            mae += CAMF_CC(configureFile,trainData,testData)
        return mae/10


if __name__ == '__main__':
        userIdDict = dict()
        itemIdDict = dict()
        categoryIdDict = dict()        
        data = list()

	configureFile = 'camf-cc.conf'
	dataFile = 'Context_LDOS-CoMoDa dataset'+path.sep+'LDOS-CoMoDa.xls'
        dataBook = xlrd.open_workbook(dataFile)
	table = dataBook.sheet_by_index(0)
	rowsLen = table.nrows
	user_set = set()
	item_set = set()
	category_set= set()
	for i in range(1,rowsLen):
		row=table.row_values(i)
		user_set.add(row[0])
		item_set.add(row[1])
		category_set.add(row[23])
                data.append(row)
        
        userIdList = list(user_set)
        userIdList.sort()
        for  index,userId in enumerate(userIdList):
            userIdDict[userId]=index

        itemIdList = list(item_set)
        itemIdList.sort()
        for  index,itemId in enumerate(itemIdList):
            itemIdDict[itemId]=index

        categoryIdList = list(category_set)
        categoryIdList.sort()
        for  index,categoryId in enumerate(categoryIdList):
            categoryIdDict[categoryId]=index

	fi = open(configureFile,'r')
	lines = fi.readlines()
        userNum = int(lines[1].split('=')[1])
        itemNum = int(lines[2].split('=')[1])
        factorNum = int(lines[3].split('=')[1])
        learnRate = float(lines[4].split('=')[1])
        regularization = float(lines[5].split('=')[1])
        categoryNum = int(lines[6].split('=')[1])
        contextNum = list()
	for i in range(7,19):
                contextNum.append(int(lines[i].split('=')[1]))
        fi.close()

        startTime = time.time() 
        ans=TenFloadValidate(data)
        endTime = time.time()
        costTime = endTime-startTime
        print 'final mae is ',ans
        print 'total use time is ',costTime
        print 'CAMF_CC finished!'


