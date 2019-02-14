import os
import json
import fnmatch
from pprint import pprint
import cv2
from region2mask import Polygon2Mask,Circle2Mask,CaculateArea,getPolygonCorners,getBoundingBox,circle2Polygon,corners2xy,rect2PolygonCorners
from time import gmtime, strftime
from random import randint
from utils import getRegionLabelDic,getJsonFiles
import numpy as np
from skimage.draw import polygon
import PIL.Image as Image

def cutMainROI(img):
	x=img[img.shape[0]/2,:,:].sum(1)
	r=0
	print img.shape
	print x
	for v in x:
		if v>20:
			r+=1
	print r
	s_x = 0
	s_y = 0
	if img.shape[0]<r:
		return img,s_x,s_y
	s_x = (img.shape[1]-r)/2
	s_y = (img.shape[0]-r)/2
	
	print s_x
	print s_y
	cut_img = img[int(s_y):int(s_y+r),int(s_x):int(s_x+r)]
	print cut_img.shape
	return cut_img,s_x,s_y

def cutMainROI1(img):
	x=img[img.shape[0]/2,:,:].sum(1)
	xx = img[img.shape[0]/2,:,:]
	yy = img[:,img.shape[1]/2,:]
	x_s = 0
	x_e = 0
	threshold = 10
	for i in range(len(xx)):
		if not (xx[i][0]<10 and xx[i][1]<10 and xx[i][2]<10):
			x_s = i
			break 
	for i in range(len(xx)):
		if not (xx[len(xx)-i-1][0]<10 and xx[len(xx)-i-1][1]<10 and xx[len(xx)-i-1][2]<10):
			x_e = len(xx)-i
			break 
	y_s = 0
	y_e = 0
	for i in range(len(yy)):
		if not (yy[i][0]<10 and yy[i][1]<10 and yy[i][2]<10):
			y_s = i
			break 
	
	for i in range(len(yy)):
		if not (yy[len(yy)-i-1][0]<10 and yy[len(yy)-i-1][1]<10 and yy[len(yy)-i-1][2]<10):
			y_e = len(yy)-i
			break
	print [y_s,y_e,x_s,x_e]
	cut_img = img[int(y_s):int(y_e),int(x_s):int(x_e)]
	return cut_img,x_s,y_s

#-----------get dictionary of region label
def getRegionLabelDic(dic_file_path,split_key,index):
	region_labels = []
	region_label_file = open(dic_file_path)
	line = region_label_file.readline()
	while line:
		word_list = line.split(split_key)
		region_labels.append(word_list[index])
		line = region_label_file.readline()
	region_label_file.close()
	return region_labels


def getJsonFiles(dataset_path = '../DR_COCO3'):
	matches = []
	paths = []
	for root, dirnames, filenames in os.walk(dataset_path):
		for filename in fnmatch.filter(filenames, 'via_region_data*.json'):
			matches.append(os.path.join(root, filename))
			paths.append(root)	
	return matches, paths
def segToMask( s, h, w, mask, value):

    N = len(s)
    rr, cc = polygon(np.array(s[1:N:2]).clip(max=h-1), \
        np.array(s[0:N:2]).clip(max=w-1)) # (y, x)
    mask[rr, cc] = value
    return mask
print('searching json...')
matches, paths = getJsonFiles()

print('transfer formate...')
#coco style data
coco_data = {}
coco_data_val = {}

dic_file_path = 'region_label_dic.txt'
region_label_dic = getRegionLabelDic(dic_file_path,'-',1)

region_label_dic_id = 0
coco_data['categories'] = []
coco_data['images'] = []
coco_data['annotations'] = []

coco_data_val['categories'] = []
coco_data_val['images'] = []
coco_data_val['annotations'] = []
region_label_dic_id = 1
for region_label in region_label_dic:
	coco_data['categories'].append({'id':region_label_dic_id,
									'name':region_label,
									'supercategory':region_label})
	coco_data_val['categories'].append({'id':region_label_dic_id,
									'name':region_label,
									'supercategory':region_label})
	region_label_dic_id+=1
image_id_c = 0
region_id = 0
dir_count = 0
circle_num = 32
log_file = open('log.txt','w')
category_id_todo = [0,1,2,3,4,5,6,7,8,9,10]

category_train_st = [0,0,0,0,0,0,0,0,0,0,0]
category_val_st = [0,0,0,0,0,0,0,0,0,0,0]
trainlst = open('./annotations/train.lst','w')
vallst = open('./annotations/val.lst','w')
random_v = -1
flag_v = -1
mode_v = 5
flip_img_base_number = 100000
flip_region_base_number = 1000000
flip = True

train_file_list = open('train.txt','w')
val_file_list = open('val.txt','w')


def create_classification(img,bbox,fi,folder,id,label):
	if not os.path.exists(folder):
		os.mkdir(folder)
	fi.write(str(id)+'.jpg \n')
	region_img = img[int(bbox[1]):int(bbox[1]+bbox[3]),int(bbox[0]):int(bbox[0]+bbox[2])]
	cv2.imwrite(folder+'/'+str(id)+'.jpg',region_img)


for file_dir in matches:
	with open(file_dir) as orig_data_file:
		data = json.load(orig_data_file)
		for image_id in data:
			#print(paths[dir_count])
			img_path = 'images/'+data[image_id]['filename']
			img_o = cv2.imread(img_path)
			if not os.path.isfile(img_path):
				log_file.write(img_path+'---load error!\n')
			else:
				filelst = ''
				#print(img_path)
				img,s_x,s_y = cutMainROI1(img_o)
				height, width= img.shape[:2]
				date_captured = strftime("%Y-%m-%d %H:%M:%S", gmtime())
				
				flag_v = image_id_c - image_id_c%mode_v
				
				if image_id_c%mode_v==0:
					random_v = randint(0,mode_v-1)
					
				if flag_v+random_v == image_id_c:
					file_name = 'val_'+str(image_id_c)+'_'+data[image_id]['filename']
					filelst = './val2014/'+file_name
					cv2.imwrite('./val2014/'+file_name,img)	
					coco_data_val['images'].append({'coco_url':img_path,
												'date_captured':date_captured,
												'flickr_url':img_path,
												'file_name':file_name,
												'id':image_id_c,
												'height':height,
												'width':width,
												'license':0})
					if flip:							
						flip_img =	cv2.flip(img,1)
						flip_file_name = 'flip_'+file_name
						cv2.imwrite('./val2014/'+flip_file_name,flip_img)	
						flipfilelst = './val2014/'+flip_file_name
						coco_data_val['images'].append({'coco_url':img_path,
													'date_captured':date_captured,
													'flickr_url':img_path,
													'file_name':flip_file_name,
													'id':image_id_c+flip_img_base_number,
													'height':height,
													'width':width,
													'license':0})							
				else:
					file_name = 'train_'+str(image_id_c)+'_'+data[image_id]['filename']	
					filelst = './train2014/'+file_name
					cv2.imwrite('./train2014/'+file_name,img)
					coco_data['images'].append({'coco_url':img_path,
												'date_captured':date_captured,
												'flickr_url':img_path,
												'file_name':file_name,
												'id':image_id_c,
												'height':height,
												'width':width,
												'license':0})
					if flip:							
						flip_img =	cv2.flip(img,1)
						flip_file_name = 'flip_'+file_name
						cv2.imwrite('./train2014/'+flip_file_name,flip_img)
						flipfilelst = './train2014/'+flip_file_name
						coco_data['images'].append({'coco_url':img_path,
													'date_captured':date_captured,
													'flickr_url':img_path,
													'file_name':flip_file_name,
													'id':image_id_c+flip_img_base_number,
													'height':height,
													'width':width,
													'license':0})					
				labels_mask = np.zeros((height,width),dtype = np.uint32)
				instances_mask = np.zeros((height,width),dtype = np.uint32)
				instances_count = np.zeros(len(category_id_todo))
				for region in data[image_id]['regions']:
					for region_attribute in data[image_id]['regions'][region]['region_attributes']:
						if data[image_id]['regions'][region]['region_attributes'][region_attribute]=='default' or data[image_id]['regions'][region]['region_attributes'][region_attribute]=='Fovea':
							continue
						#category_id = region_label_dic.index(data[image_id]['regions'][region]['region_attributes'][region_attribute])+1
						id_count=0
						category_id=0
						for region_label in region_label_dic:
							id_count+=1
							if region_label in data[image_id]['regions'][region]['region_attributes'][region_attribute]:
								category_id=id_count
								break
						if category_id==0:
							print 'error:category_id is 0'
							print data[image_id]['regions'][region]['region_attributes'][region_attribute]
							continue
						if category_id in category_id_todo:
							bad_region = 0
							circle_ca = ['big_circle','small_circle','circle','ellipse']
							if data[image_id]['regions'][region]['shape_attributes']['name'] in circle_ca:
								#print(data[image_id]['regions'][region]['shape_attributes']['name'])
								#print(data[image_id]['regions'][region]['shape_attributes'])
								r =0
								if data[image_id]['regions'][region]['shape_attributes']['name'] =='big_circle':
									if width<1000:

										r = int(80 *float(width)/1600+20);
									else:
										r = int(80 *float(width)/1600);
									
								elif data[image_id]['regions'][region]['shape_attributes']['name'] =='small_circle':
									if width<1000:
										r  = int(60*float(width)/1600+15);

									else:
										r  = int(60*float(width)/1600);
								elif data[image_id]['regions'][region]['shape_attributes']['name'] =='ellipse':
									r = (data[image_id]['regions'][region]['shape_attributes']['ry']+data[image_id]['regions'][region]['shape_attributes']['rx'])/2
								else:
									r = data[image_id]['regions'][region]['shape_attributes']['r']
								if 'Microaneurysms' in data[image_id]['regions'][region]['region_attributes'][region_attribute]:
									print 'r:'+str(r)
									if r>35:
										r = r/2
										print 'fixed r'
								if '(Hemorrhages)' in data[image_id]['regions'][region]['region_attributes'][region_attribute]:
									print 'r:'+str(r)
									r = r*2/3
									print 'fixed r:'+str(r)
								circle = (data[image_id]['regions'][region]['shape_attributes']['cx'],
											data[image_id]['regions'][region]['shape_attributes']['cy'],
											r)
								corners = circle2Polygon(circle,circle_num)
								xy,x,y = corners2xy(corners)
								bbox = getBoundingBox(x,y)
								area = CaculateArea(Polygon2Mask([width,height],corners,category_id+1))
								if area ==0:
									print('stoped:'+str(data[image_id]['regions'][region]['shape_attributes']))
									print('---:'+str(circle))
								if bbox[2]==0 or bbox[3]==0:
									bad_region=1								
							elif data[image_id]['regions'][region]['shape_attributes']['name']=='rect':
								rect = [data[image_id]['regions'][region]['shape_attributes']['x'],
										data[image_id]['regions'][region]['shape_attributes']['y'],
										data[image_id]['regions'][region]['shape_attributes']['width'],
										data[image_id]['regions'][region]['shape_attributes']['height']]
								bbox = rect
								corners = rect2PolygonCorners(rect)
								xy,x,y = corners2xy(corners)
								area = CaculateArea(Polygon2Mask([width,height],corners,category_id+1))
								if bbox[2]==0 or bbox[3]==0:
									bad_region=1								
							elif data[image_id]['regions'][region]['shape_attributes']['name']=='polygon':
								x = data[image_id]['regions'][region]['shape_attributes']['all_points_x']
								y = data[image_id]['regions'][region]['shape_attributes']['all_points_y']
								corners = getPolygonCorners(x,y)
								area = CaculateArea(Polygon2Mask([width,height],corners,category_id+1))
								xy,tx,ty = corners2xy(corners)
								bbox = getBoundingBox(x,y)
								if bbox[2]==0 or bbox[3]==0:
									bad_region=1
															
							if bad_region == 0:

								for index_xy in range(len(xy)):
									if index_xy%2==0:
										xy[index_xy]-=s_x
									else:
										xy[index_xy]-=s_y

									if xy[index_xy]<0:
										xy[index_xy] = 0 
								bbox[0]=bbox[0]-s_x
								bbox[1]=bbox[1]-s_y
								if bbox[0]<0:
									bbox[0]=0
								if bbox[1]<0:
									bbox[1]=0
								if flip:
									flip_xy = xy
									flip_bbox = bbox[:]									
									for index_xy in range(len(flip_xy)):
										if index_xy%2==0:
											flip_xy[index_xy] = width - flip_xy[index_xy]-1
									flip_bbox[0] = width - flip_bbox[0]-flip_bbox[2] -1	
								if flag_v+random_v == image_id_c:
									category_val_st[category_id_todo.index(category_id)]+=1	
									coco_data_val['annotations'].append({'id':region_id,
																	 'image_id':image_id_c,
																	 'category_id':category_id,
																	 'iscrowd':0,
																	 'area':area,
																	 'bbox':bbox,
																	 'segmentation':[xy]})
									create_classification(img,bbox,val_file_list,'val',region_id,category_id-1)
									if flip:
										coco_data_val['annotations'].append({'id':region_id+flip_region_base_number,
																		'image_id':image_id_c+flip_img_base_number,
																		'category_id':category_id,
																		'iscrowd':0,
																		'area':area,
																		'bbox':flip_bbox,
																		'segmentation':[flip_xy]})
										create_classification(flip_img,bbox,val_file_list,'val',region_id,category_id-1)										
								else:
									category_train_st[category_id_todo.index(category_id)]+=1
									coco_data['annotations'].append({'id':region_id,
																	 'image_id':image_id_c,
																	 'category_id':category_id,
																	 'iscrowd':0,
																	 'area':area,
																	 'bbox':bbox,
																	 'segmentation':[xy]})
									create_classification(img,bbox,train_file_list,'train',region_id,category_id-1)
									if flip:
										coco_data['annotations'].append({'id':region_id+flip_region_base_number,
																		'image_id':image_id_c+flip_img_base_number,
																		'category_id':category_id,
																		'iscrowd':0,
																		'area':area,
																		'bbox':flip_bbox,
																		'segmentation':[flip_xy]})
										create_classification(flip_img,bbox,train_file_list,'train',region_id,category_id-1)																		
								labels_mask = segToMask(xy,height,width,labels_mask,category_id)
								instances_mask = segToMask(xy,height,width,instances_mask,category_id*1000+instances_count[category_id])
								instances_count[category_id] += 1
								region_id+=1
				save_folder = ''
				if flag_v+random_v == image_id_c:
					save_folder = './val2014/'
					lstline = str(image_id_c) + '\t' +filelst+'\t'+save_folder+str(image_id_c)+'_labelIds.png\n'
					vallst.write(lstline)
				else:
					save_folder = './train2014/'
					lstline = str(image_id_c) + '\t' +filelst+'\t'+save_folder+str(image_id_c)+'_labelIds.png\n'
					trainlst.write(lstline)
				labels_mask_im = Image.fromarray(labels_mask)
				labels_mask_im.save(save_folder+str(image_id_c)+'_labelIds.png')
				instances_mask_im = Image.fromarray(instances_mask)
				instances_mask_im.save(save_folder+str(image_id_c)+'_instanceIds.png')
				image_id_c+=1
	dir_count+=1	

train_file_list.close()
val_file_list.close()

log_file.close()
vallst.close()
trainlst.close()
print('save file...')

with open('./annotations/instances_train2014.json', 'w') as outfile:  
    json.dump(coco_data, outfile)
    outfile.close()

with open('./annotations/instances_val2014.json', 'w') as outfile:  
    json.dump(coco_data_val, outfile)
    outfile.close()

print('total_images:'+str(image_id_c))
print('total_regions:'+str(region_id))
print('train:'+str(category_train_st))
print('val:'+str(category_val_st))
