#coding=utf-8
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from zhishiren2020.models import Yonghu,Qunzu,Wenji,Wenduan,Fujian,Biaoqian,Tongji,Alljishu,Fayanmima,Caozuo,Liaodata,Liaolist
from zhishiren2020.shangchuan import upload1
from datetime import datetime,timedelta
from pyDes import des, PAD_PKCS5, ECB
import binascii,json,os,random,xlrd,base64
# mongo查询的结果中，objectId无法通过json序列化，解决方案：
from bson import json_util
from django.utils import timezone
from django.db.models import Q
from django.db.models import F
from django.forms.models import model_to_dict
import itertools
from itertools import chain
from operator import attrgetter

# News.objects.to_json()这是对mongodb的模型的查询的序列化，与mysql不同，更方便
# News.objects.count()这是对mongodb的模型的查询的计数
def index(request):
    return render(request, 'index.html')
    
#这是接受前端传递的id串，拆分成数组的形式，用来带入查询关注用户的动态，关注知识点的动态，
def chuan_chaifen(chuan,type0):
    cz1=chuan.split('_'); 
    cz2=[]
    for k in cz1:
        if k =='' or k == None:
            pass
        else:
            k=int(k)
            if k>90000000 and k<99999999 and type0=='yh':
                cz2.append(k)
            if k>80000000 and k<90000000 and type0=='qz':
                cz2.append(k)
            if (k<80000000 and type0=='zhi') or (k>100000000 and type0=='zhi'):
                cz2.append(k)
            if k>30000000 and k<40000000 and type0=='bq':
                cz2.append(k)
            if k>10000000 and k<20000000 and type0=='wj':
                cz2.append(k)
            if k>20000000 and k<30000000 and type0=='wd':
                cz2.append(k)
    return cz2
    
    
    #这是用于用户登录时读取用户关注的、用户加入的群组ID列表，然后把其中的元素链接成一段字符串，然后再发送给前端cookie保存
def genxin_idchuan(userid):
    cz1=Caozuo.objects.filter(
        Q(cztype='加入群组',fystatus="正常有效",uid0=userid)|
        Q(cztype='关注',fystatus="正常有效",uid0=userid)|
        Q(cztype='关注',fystatus="正在审核",uid0=userid)).values('id0')
    userid=str(userid)
    array1 = "90000000_"
    for l1 in cz1:
        k1=str(l1['id0'])
        array1 =array1+k1 +"_"
    return array1
    # return request.session.get('sessionchuan', array1)
    
    #这是用于转换id与代表的知识点类型，例如在前端“加标签”“关联”等功能，输入id后，到后台变成相关知识点的标题和类型
def id_transfer(cz_id0):
    if cz_id0>10000000 and cz_id0<20000000:
        cz_type0="wenjiye"
        wenji1=Wenji.objects.get(wj_id=cz_id0)
        cz_title0=wenji1.wj_title
    if cz_id0>20000000 and cz_id0<30000000:
        cz_type0="wenduanye"
        wenduan1=Wenduan.objects.get(wd_id=cz_id0)
        cz_title0=wenduan1.wj_title+wenduan1.wd_title
    if cz_id0>30000000 and cz_id0<40000000:
        cz_type0="biaoqianye"
        biaoqian1=Biaoqian.objects.get(bq_id=cz_id0)
        cz_title0=biaoqian1.bq_title
    if cz_id0>80000000 and cz_id0<90000000:
        cz_type0="qunzuye"
        qunzu1=Qunzu.objects.get(qz_id=cz_id0)
        cz_title0=qunzu1.qz_title
    if cz_id0>90000000 and cz_id0<100000000:
        cz_type0="yonghuye"
        yonghu1=Yonghu.objects.get(yonghu_id=cz_id0)
        cz_title0=yonghu1.yonghu_name
    if cz_id0>100000000 and cz_id0<200000000:
        cz_type0="fayanye"
        fayan1=Caozuo.objects.get(czid=cz_id0)
        cz_title0=fayan1.fyshen
    return cz_type0,cz_title0


#！！！这是最主要的功能，对应前端中用户分享关注加标签等操作，
@csrf_exempt
def to_caozuo(request):
    data = json.loads(request.body)

    cz_type  = data.get('cztype')
    # fymm=int(data.get('fymm'))
    fymm=data.get('fymm')#这是发言密码的意思。
    fy_  = data.get('fy')
    mi_yn = data.get('fymi')
    fy_niming = data.get('fyniming')
    fy_type=data.get('fytype')
    fy_att=data.get('fyatt')
    fy_fanwei_fx=data.get('fyfanwei_fx')
    fy_fanwei=data.get('fyfanwei')
    bq_id=data.get('bq_id')
    id_0=data.get('id0')
    title_0=data.get('title0')
    type_0=data.get('type0')
    id_1=data.get('id1')
    u_id=int(data.get('uid'))#以下的uid0和uid1分别对应对内和对外的ID，传到前台的是uid1
    u_name=data.get('uname')
    fy_=fy_.replace("请输入发言/附言的内容。","")
    fy_=fy_.replace("请输入你要发言的内容。","")

    if mi_yn==1:#加密的明文信息，现将发言内容暂时存在fyshen中，待审批通过之后，在转入fy中。
        fystatus='正常有效'
        fymi=len(fy_)
        DES_SECRET_KEY = fymm
        fy = fy_.encode('gb2312')# # 这里中文要转成字节， 英文好像不用
        des_obj = des(DES_SECRET_KEY, ECB, DES_SECRET_KEY, padmode=PAD_PKCS5)  # 初始化一个des对象
        fy = des_obj.encrypt(fy)   # 用对象的encrypt方法加密
        fy = base64.b64encode(fy)
        fyshen=''
    else:
        fystatus='正在审核'
        fymi=0
        fyshen=fy_
        fy='正在审核'
        
    if cz_type=='关注':
        cz1 = Caozuo.objects.filter(uid0=u_id,id0=id_0,cztype='关注')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            cz0=Caozuo(
                cztype = '关注',
                fy = fy,
                fyshen=fyshen,
                fymi = fymi,
                fystatus=fystatus,
                
                id0 = id_0,
                title0 = title_0,
                type0 =  type_0,

                uid0 = u_id,
                uid1 = u_id,
                uname = u_name,
                time0 = datetime.now(),
                time1 = datetime.now(),
            )
            cz0.save()
            #这里不需要统计用户id相关，因为在chuan中体现
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.guanzhu=yh_tongji.guanzhu+1
            yh_tongji.save()

    if cz_type=='关联':
        cz1 = Caozuo.objects.filter(id0=id_0,id1=id_1,cztype='关联')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            type_1,title_1=id_transfer(int(id_1))
            cz0=Caozuo(
                cztype = '关联',
                fy = fy,
                fyshen=fyshen,
                fymi = fymi,
                fystatus=fystatus,
                
                id0 = id_0,
                title0 = title_0,
                type0 =  type_0,
                
                id1 = id_1,
                title1 = title_1,
                type1 =  type_1,
                
                fyatt=fy_att,

                uid0 = u_id,
                uid1 = u_id,
                uname = u_name,
                time0 = datetime.now(),
                time1 = datetime.now(),
            )
            cz0.save()
            alljishu = Alljishu.objects.get(keyid=999)
            alljishu.fuyan=alljishu.fuyan+1
            alljishu.save()
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.guanlian=yh_tongji.guanlian+1
            yh_tongji.save()

    if cz_type=='加入标签':
        id_1=int(bq_id[0:8])
        title_1=bq_id[8:-8]
        type_1='biaoqianye'
        fy_fanwei=int(bq_id[-8:])
        
        cz1 = Caozuo.objects.filter(id0=id_0,id1=id_1,cztype='加入标签')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            cz0=Caozuo(
                cztype = '加入标签',
                fy = fy,
                fyshen=fyshen,
                fymi = fymi,
                fystatus=fystatus,
                
                id0 = id_0,
                title0 = title_0,
                type0 =  type_0,
                
                id1 = id_1,
                title1 = title_1,
                type1 =  type_1,
                
                uid0 = u_id,
                uid1 = u_id,
                uname = u_name,
                time0 = datetime.now(),
                time1 = datetime.now(),
            )
            cz0.save()
            alljishu = Alljishu.objects.get(keyid=999)
            alljishu.fuyan=alljishu.fuyan+1
            alljishu.save()
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.biaoqian=yh_tongji.biaoqian+1
            yh_tongji.save()
            yh_tongji = Tongji.objects.get(tjid=id_1)
            yh_tongji.neihan=yh_tongji.neihan+1
            yh_tongji.save()

    if cz_type=='标签里加入':
        cz1 = Caozuo.objects.filter(id0=id_1,id1=id_0,cztype='加入标签')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            type_1,title_1=id_transfer(int(id_1))
            cz0=Caozuo(
                cztype = '加入标签',
                fy = fy,
                fyshen=fyshen,
                fymi = fymi,
                fystatus=fystatus,
                
                id0 = id_1,
                title0 = title_1,
                type0 =  type_1,
                
                id1 = id_0,
                title1 = title_0,
                type1 =  type_0,
                
                uid0 = u_id,
                uid1 = u_id,
                uname = u_name,
                time0 = datetime.now(),
                time1 = datetime.now(),
            )
            cz0.save()
            alljishu = Alljishu.objects.get(keyid=999)
            alljishu.fuyan=alljishu.fuyan+1
            alljishu.save()
            yh_tongji = Tongji.objects.get(tjid=id_1)
            yh_tongji.biaoqian=yh_tongji.biaoqian+1
            yh_tongji.save()
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.neihan=yh_tongji.neihan+1
            yh_tongji.save()

    if cz_type=='评论' or cz_type=='评价':
        if fy_niming == '匿名':
            uid1=90000000
            uname='匿名'
        else:
            uid1=u_id
            uname=u_name
        
        id_0=int(id_0)
        if id_0>100000000:
            cz_ = Caozuo.objects.get(czid=id_0)
            fyhui=cz_.fy
            title_0=cz_.fymi

        cz0=Caozuo(
            cztype = cz_type,
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,
            fyatt=fy_att,
            
            id0 = id_0,
            title0 = title_0,
            type0 =  type_0,
            
            fyhui=fyhui,
            
            uid0 = u_id,
            uid1 = uid1,
            uname = uname,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        id_0=int(id_0)
        print(id_0)
        if id_0<100000000:
            alljishu = Alljishu.objects.get(keyid=999)
            alljishu.fuyan=alljishu.fuyan+1
            alljishu.save()
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.pinglun=yh_tongji.pinglun+1
            yh_tongji.save()
        else:
            if type_0!='fayanye':#评论对象是附言
                cz2=Caozuo.objects.get(czid=id_0)
                cz2.hui=cz2.hui+1
                cz2.save()
            if type_0=='fayanye':#评论对象是提问，发言等
                cz2=Caozuo.objects.get(czid=id_0)
                cz2.hui=cz2.hui+1
                cz2.save()
                yh_tongji = Tongji.objects.get(tjid=id_0)
                yh_tongji.pinglun=yh_tongji.pinglun+1
                yh_tongji.save()


    if cz_type=='发言' or cz_type=='群发言' or cz_type=='发言列表':
        cz0=Caozuo(
            cztype = '发言',
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,
            
            fyatt=fy_att,
            fytype=fy_type,
            # id0 = id_0,
            # title0 = 'fayanye',
            type0 =  'fayanye',
            
            fyfanwei=fy_fanwei,
            
            uid0 = u_id,
            uid1 = u_id,
            uname = u_name,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        tongji =Tongji(tjid=cz0.czid)
        tongji1=tongji.save()
        yh_tongji = Tongji.objects.get(tjid=u_id)
        yh_tongji.zengfayan=yh_tongji.zengfayan+1
        yh_tongji.save()


    if cz_type=='提问' or cz_type=='提问列表':
        if fy_niming == '匿名':
            uid1=90000000
            uname='匿名'
        else:
            uid1=u_id
            uname=u_name
        
        if id_0!=0:
            type_0,title_0=id_transfer(int(id_0))
        else:
            type_0=''
            title_0=''
        
        cz0=Caozuo(
            cztype = '提问',
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,
            
            fytype=fy_type,
            type0='fayanye',
            
            id1 = id_0,
            title1 = title_0,
            type1 =  type_0,
            
            fyfanwei=90000000,
            
            uid0 = u_id,
            uid1 = uid1,
            uname = uname,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        tongji =Tongji(tjid=cz0.czid)
        tongji1=tongji.save()
        # yh_tongji = Tongji.objects.get(tjid=u_id)
        # yh_tongji.zengfayan=yh_tongji.zengfayan+1
        # yh_tongji.save()


    if cz_type=='分享':
        cz0=Caozuo(
            cztype = '分享',
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,
            
            fyatt=fy_att,

            id0 = id_0,
            title0 = title_0,
            type0 =  type_0,
            
            fyfanwei=fy_fanwei_fx,
            
            uid0 = u_id,
            uid1 = u_id,
            uname = u_name,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        yh_tongji = Tongji.objects.get(tjid=id_0)
        yh_tongji.fenxiang=yh_tongji.fenxiang+1
        yh_tongji.save()
        yh_tongji = Tongji.objects.get(tjid=u_id)
        yh_tongji.zengfenxiang=yh_tongji.zengfenxiang+1
        yh_tongji.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.fuyan=alljishu.fuyan+1
        alljishu.save()

    if cz_type=='纠错':
        cz0=Caozuo(
            cztype = '纠错',
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,

            id0 = id_0,
            title0 = title_0,
            type0 =  type_0,
            
            uid0 = u_id,
            uid1 = u_id,
            uname = u_name,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()

    if cz_type=='发言密码':
        cz0=Caozuo(
            cztype = '发言密码',
            fy = fyshen,
            fymi = 0,
            fystatus='正常有效',
            
            id0 = u_id,
            id1 = id_1,

            uid0 = u_id,
            uid1 = u_id,
            uname = u_name,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        
    if cz_type=='添加段落':
        wd0 = Wenduan.objects.filter(wj_id=id_0).order_by('wj_xuhao').last()
        if wd0:
            xuhao=wd0.wj_xuhao+1
        else:
            xuhao=1
        fyshen=fyshen.replace("请输入段落内容。","")
        cz0=Wenduan(
            wj_id = id_0,
            wj_title=title_0,
            wj_xuhao=xuhao,
            
            wd_title = id_1,
            wd_content=fyshen,

            wd_createrid = u_id,
            wd_manager = u_id,
            wd_creatername= u_name,
            wd_createtime = datetime.now(),
        )
        cz0.save()
        tongji =Tongji(tjid=cz0.wd_id)
        tongji1=tongji.save()
        # yh_tongji = Tongji.objects.get(tjid=id_0)
        # yh_tongji.neihan=yh_tongji.neihan+1
        # yh_tongji.save()
        wj0 = Wenji.objects.get(wj_id=id_0)
        wj0.wj_wdshu=wj0.wj_wdshu+1
        wj0.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.wenduan=alljishu.wenduan+1
        alljishu.save()
        
        
    if cz_type=='公告':
        cz0=Caozuo(
            cztype = '公告',
            fy = fy,
            fyshen=fyshen,
            fymi = fymi,
            fystatus=fystatus,
            
            uid0 = u_id,
            uid1 = u_id,
            uname = u_name,
            time0 = datetime.now(),
            time1 = datetime.now(),
        )
        cz0.save()
        
    if cz_type=='加入群组':
        id_0=int(id_0)
        id_1=int(id_1)
        cz1 = Caozuo.objects.filter(id0=id_0,uid0=u_id,cztype='加入群组')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            qunzu1=Qunzu.objects.get(qz_id=id_0)
            if id_1==int(qunzu1.qz_kouling):
                cz0=Caozuo(
                    cztype ='加入群组',
                    fy = fyshen,
                    fyshen=fyshen,
                    fymi = fymi,
                    fystatus='正常有效',
                    
                    id0 = id_0,
                    title0 = title_0,
                    type0 =  type_0,
                    
                    uid0 = u_id,
                    uid1 = u_id,
                    uname = u_name,
                    time0 = datetime.now(),
                    time1 = datetime.now(),
                )
                cz0.save()
                yh_tongji = Tongji.objects.get(tjid=id_0)
                yh_tongji.neihan=yh_tongji.neihan+1
                yh_tongji.save()
                #这里不需要统计用户id相关，因为在chuan中体现
            else:
                b={"msg":6}#加入群组的密码不正确！
                return JsonResponse(b, safe=False)
            
    if cz_type=='邀请':
        id_0=int(id_0)#这是群组号
        id_1=int(id_1)#这是“被邀请用户”的用户号
        cz_type1,cz_title1=id_transfer(id_1)
        cz1 = Caozuo.objects.filter(id0=id_0,uid0=id_1,cztype='加入群组')
        cz1=cz1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
        if cz1.exists():
            b={"msg":7}
            return JsonResponse(b, safe=False)
        else:
            cz0=Caozuo(
                cztype ='加入群组',
                fy = '你被管理员邀请加入该群',
                fyshen=fyshen,
                fymi = fymi,
                fystatus='正常有效',
                
                id0 = id_0,
                title0 = title_0,
                type0 =  type_0,
                
                id1 = u_id,
                
                uid0 = id_1,
                uid1 = id_1,
                uname = cz_title1,
                
                time0 = datetime.now(),
                time1 = datetime.now(),
            )
            cz0.save()
            yh_tongji = Tongji.objects.get(tjid=id_0)
            yh_tongji.neihan=yh_tongji.neihan+1
            yh_tongji.save()
            #这里不需要统计用户id相关，因为在chuan中体现

    if cz0:
        if cz_type=='关注' or cz_type=='加入群组':
            b={"msg":1,"focused_id":cz0.czid}
            return JsonResponse(b, safe=False)
        else:
            b={"msg":1}
            return JsonResponse(b, safe=False)
    else:
        b={"msg":2}
        return JsonResponse(b, safe=False)
        # try:
        #     cz0.save()
        #     # tongji1 = Tongji.objects.get(tjid=zhi_id)
        #     # tongji1.guanzhu=tongji1.guanzhu+1
        #     # tongji1.save()
        #     b={"ok_id":0}
        #     return JsonResponse(b, safe=False)
        # except:
        #     b={"ok_id":2}
        #     return JsonResponse(b, safe=False)

        # tongji1 = Tongji.objects.get(tjid=zhi_id)
        # tongji1.guanzhu=tongji1.guanzhu+1
        # tongji1.save()

#！！！这是知识点管理员修改知识点的
@csrf_exempt
def to_chongfa(request):
    data = json.loads(request.body)
    kkk= data.get('czid')
    kkk=int(kkk)
    cz1 = Caozuo.objects.get(czid=kkk)
    cz1.time1=datetime.now()
    cz1.time0=datetime.now()
    cz1.save()
    b={"msg":0,"new_wentime":datetime.now()}
    return JsonResponse(b, safe=False)
    
#！！！这是知识点管理员修改知识点的
@csrf_exempt
def to_xiugai(request):
    data = json.loads(request.body)
    kkk= data.get('kkk')
    id0= data.get('id0')
    uid= data.get('uid')
    zhitype= data.get('zhitype')
    
    newfanwei= data.get('newfanwei')
    xx_status= data.get('xx_status')
    fyatt= data.get('fyatt')
    diqu= data.get('diqu')
    hangye= data.get('hangye')
    fawenjigou= data.get('fawenjigou')
    born_time= data.get('born_time')
    dead_time= data.get('dead_time')
    newtype= data.get('newtype')
    kouling0= data.get('kouling0')
    shuoming= data.get('shuoming')
    time0=datetime.now()
    fyhui=''
    kkkstatus=''

    if kkk=='xx_status':
        if zhitype=='wenjiye':
            wj0 = Wenji.objects.get(wj_id=id0)
            fy='状态：'+wj0.wj_status
            wj0.wj_status=xx_status
            wj0.save()
        if zhitype=='fayanye':
            fy0 = Caozuo.objects.get(czid=id0)
            fy='状态：'+fy0.fystatus
            fy0.fystatus=xx_status
            fy0.save()
        if zhitype=='qunzuye':
            qz0 = Qunzu.objects.get(bq_id=id0)
            fy='状态：'+qz0.qz_status
            qz0.qz_status=xx_status
            qz0.save()
        if zhitype=='biaoqianye':
            bq0 = Biaoqian.objects.get(bq_id=id0)
            fy='状态：'+bq0.bq_status
            bq0.bq_status=xx_status
            bq0.save()
    if kkk=='xx_type':
        if zhitype=='wenjiye':
            wj0 = Wenji.objects.get(wj_id=id0)
            fy='文件类型：'+wj0.wj_type
            wj0.wj_type=newtype
            wj0.save()
        if zhitype=='fayanye':
            fy0 = Caozuo.objects.get(czid=id0)
            fy='发言类型：'+fy0.fytype
            fy0.fytype=newtype
            fy0.save()
        if zhitype=='qunzuye':
            qz0 = Qunzu.objects.get(bq_id=id0)
            fy='群组类型：'+qz0.qz_type
            qz0.qz_type=newtype
            qz0.save()
    if kkk=='newfanwei':
        if zhitype=='wenjiye':
            wj0 = Wenji.objects.get(wj_id=id0)
            fy='公开范围：'+str(wj0.wj_fanwei)
            wj0.wj_fanwei=newfanwei
            wj0.save()
        if zhitype=='wenduanye':
            wd0 = Wenduan.objects.get(wd_id=id0)
            wj0=Wenji.objects.get(wj_id=wd0.wj_id)
            fy='公开范围：'+str(wj0.wj_fanwei)
            wj0.wj_fanwei=newfanwei
            wj0.save()
        if zhitype=='fayanye':
            fy0 = Caozuo.objects.get(czid=id0)
            fy='公开范围：'+str(fy0.fyfanwei)
            fy0.fyfanwei=newfanwei
            fy0.save()
        if zhitype=='biaoqianye':
            bq0 = Biaoqian.objects.get(bq_id=id0)
            fy='公开范围：'+str(bq0.bq_fanwei)
            bq0.bq_fanwei=newfanwei
            bq0.save()
    if kkk=='shuoming':
        if zhitype=='wenjiye':
            wj0 = Wenji.objects.get(wj_id=id0)
            fy='文件说明：'
            fyhui=wj0.wj_remark
            wj0.wj_remark=shuoming
            wj0.save()
        if zhitype=='wenduanye':
            wd0 = Wenduan.objects.get(wd_id=id0)
            fy='文件说明：'
            fyhui=wd0.wd_content
            wd0.wd_content=shuoming
            wd0.save()
        if zhitype=='fayanye':
            fy0 = Caozuo.objects.get(czid=id0)
            fy='发言内容：'
            fyhui=fy0.fyshen
            fy0.fy=shuoming
            fy0.fyshen=shuoming
            fy0.save()
        if zhitype=='biaoqianye':
            bq0 = Biaoqian.objects.get(bq_id=id0)
            fy='标签说明：'
            fyhui=bq0.bq_remark
            bq0.bq_remark=shuoming
            bq0.save()
        if zhitype=='qunzuye':
            qz0 = Qunzu.objects.get(qz_id=id0)
            fy='群组说明：'
            fyhui=qz0.qz_remark
            qz0.qz_remark=shuoming
            qz0.save()
    if kkk=='fyatt':
        fy0 = Caozuo.objects.get(czid=id0)
        fy='发言态度：'+fy0.fyatt
        fy0.fyatt=fyatt
        fy0.save()
    if kkk=='kouling0':
        qz0 = Qunzu.objects.get(bq_id=id0)
        fy='入群口令：'+qz0.qz_kouling
        qz0.qz_kouling=kouling0
        qz0.save()
    if kkk=='born_time':
        wj0 = Wenji.objects.get(wj_id=id0)
        fy='生效日期：'
        time0=wj0.wj_borntime
        wj0.wj_borntime=born_time
        wj0.save()
    if kkk=='dead_time':
        wj0 = Wenji.objects.get(wj_id=id0)
        fy='失效日期：'
        time0=wj0.wj_deadtime
        wj0.wj_deadtime=dead_time
        wj0.save()
    if kkk=='diqu':
        wj0 = Wenji.objects.get(wj_id=id0)
        fy='所属地区：'+wj0.wj_area
        wj0.wj_area=diqu
        wj0.save()
    if kkk=='hangye':
        wj0 = Wenji.objects.get(wj_id=id0)
        fy='所属行业：'+wj0.wj_hangye
        wj0.wj_hangye=hangye
        wj0.save()
    if kkk=='fawenjigou':
        wj0 = Wenji.objects.get(wj_id=id0)
        fy='发文机构：'+wj0.wj_publisher
        wj0.wj_publisher=fawenjigou
        wj0.save()

    cz0=Caozuo(
        cztype ='修改',
        fy = fy,
        fyshen=fy,
        fyhui=fyhui,
        id0 = id0,
        uid0 = uid,
        uid1 = uid,
        time0 =time0,
        time1 = datetime.now(),
        )
    cz0.save()

    if cz0:
        yh_tongji = Tongji.objects.get(tjid=id0)
        yh_tongji.xiugai=yh_tongji.xiugai+1
        yh_tongji.save()
        b={"msg":1}
        return JsonResponse(b, safe=False)
    else:
        b={"msg":2}
        return JsonResponse(b, safe=False)
        

@csrf_exempt
def change_caozuo(request):
    data = json.loads(request.body)
    czid = data.get('czid')
    czxxx = data.get('czxxx')
    cz1=Caozuo.objects.get(czid=czid)
    try:
        cz1.fystatus=czxxx
        cz1.save()
        if czxxx=='失效已删':
            if cz1.cztype=='分享':
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.fenxiang=tongji1.fenxiang-1
                tongji1.save()
                tongji1 = Tongji.objects.get(tjid=cz1.uid0)
                tongji1.zengfenxiang=tongji1.zengfenxiang-1
                tongji1.save()
            if cz1.cztype=='关注':
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.guanzhu=tongji1.guanzhu-1
                tongji1.save()
            if cz1.cztype=='发言':
                tongji1 = Tongji.objects.get(tjid=cz1.uid0)
                tongji1.zengfayan=tongji1.zengfayan-1
                tongji1.save()
            if cz1.cztype=='加入标签':
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.biaoqian=tongji1.biaoqian-1
                tongji1.save()
                tongji1 = Tongji.objects.get(tjid=cz1.id1)
                tongji1.neihan=tongji1.neihan-1
                tongji1.save()
            if cz1.cztype=='加入群组':
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.neihan=tongji1.neihan-1
                tongji1.save()
            if cz1.cztype=='评论' and cz1.id0>100000000 and cz1.title0!='fayanye':
                #这是如果评论的是一条附言，那就给附言的caozuo记录中的hui字段加一
                cz2=Caozuo.objects.get(czid=cz1.id0)
                cz2.hui=cz2.hui-1
                cz2.save()
            if cz1.cztype=='评论' and cz1.id0>100000000 and cz1.title0=='fayanye':
                #这是如果评论的是一条附言，那就给附言的caozuo记录中的hui字段加一
                cz2=Caozuo.objects.get(czid=cz1.id0)
                cz2.hui=cz2.hui-1
                cz2.save()
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.pinglun=tongji1.pinglun-1
                tongji1.save()
            if cz1.cztype=='评论' and cz1.id0<100000000:
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.pinglun=tongji1.pinglun-1
                tongji1.save()
            if cz1.cztype=='关联':
                tongji1 = Tongji.objects.get(tjid=cz1.id0)
                tongji1.guanlian=tongji1.guanlian-1
                tongji1.save()
        b={"msg":1,"hfid0":cz1.id0}
        return JsonResponse(b, safe=False)
    except:
        b={"msg":2}
        return JsonResponse(b, safe=False)
    
    #这是用于查询用户是否已经关注和加入群组的功能
@csrf_exempt
def check_focused(request):
    data = json.loads(request.body)
    userid  = data.get('userid')
    zhi_id  = data.get('zhi_id')
    zhi_id  = int(zhi_id)
    
    userid=int(userid)

    cz1=Caozuo.objects.filter(
        Q(fystatus="正常有效",uid0=userid,id0=zhi_id,cztype="加入群组")|
        Q(fystatus="正在审核",uid0=userid,id0=zhi_id,cztype="加入群组")|
        Q(fystatus="正常有效",uid0=userid,id0=zhi_id,cztype="关注")|
        Q(fystatus="正在审核",uid0=userid,id0=zhi_id,cztype="关注")).last()
    if cz1:
        b={"focused_id":cz1.czid}
        return JsonResponse(b, safe=False)
    else:
        b={"focused_id":0}
        return JsonResponse(b, safe=False)
    
# 这是用于显示评论/评价/关联/标签/发言密码/群内用户的列表显示
@csrf_exempt
def xunhuancaozuo(request):
    data = json.loads(request.body)
    id0 = data.get('zhid')
    cztype=data.get('cztype')
    if cztype =='解答':
        cztype='评论'
    list1 =Caozuo.objects.filter(cztype=cztype,id0=id0).order_by('-time1')
    list1 =list1.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核"))
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time0','time1','ding','cai','hui','fyhui','fujianshu'))
    # b={'list':list1}
    return JsonResponse(list1,safe=False)

#这个是前端biaoqianye中标签内含内容的列表
@csrf_exempt
def xunhuanbqnei(request):
    data = json.loads(request.body)
    id1 = data.get('zhid')
    list1 =Caozuo.objects.filter(cztype="加入标签",id1=id1).order_by('-time1')
    list1 =list1.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核"))
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time0','time1','ding','cai','hui','fyhui','fujianshu'))
    # b={'list':list1}
    return JsonResponse(list1,safe=False)
    
   #这个是前端qunzuye中群组内动态的列表 
@csrf_exempt
def xunhuanqznei(request):
    data = json.loads(request.body)
    qzid = data.get('qzid')
    dongtaitype = data.get('dongtaitype')
    yonghuid = data.get('yonghuid')
    userid=int(data.get('userid'))
    chuan=data.get('chuan')
    
    if dongtaitype=='我':
        list1 =Caozuo.objects.filter(
            Q(cztype="分享",fystatus="正常有效")|
            Q(cztype="分享",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正常有效"))
        list1 =list1.filter(uid0=userid).order_by('-time1')
    if dongtaitype=='群':
        list1 =Caozuo.objects.filter(
            Q(cztype="分享",fystatus="正常有效")|
            Q(cztype="分享",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正常有效"))
        list1 =list1.filter(fyfanwei=qzid).order_by('-time1')
    if dongtaitype=='TA':
        chuan_qz=chuan_chaifen(chuan,'qz')
        chuan_qz.append(90000000)
        list1 =Caozuo.objects.filter(
            Q(cztype="分享",fystatus="正常有效")|
            Q(cztype="分享",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正常有效"))
        list1 =list1.filter(fyfanwei__in=chuan_qz,uid0=yonghuid).order_by('-time1')
    if dongtaitype=='发言列表':
        if yonghuid==userid:
            list1 =Caozuo.objects.filter(
                Q(cztype="发言",fystatus="正在审核")|
                Q(cztype="发言",fystatus="正常有效"))
            list1 =list1.filter(uid0=userid).order_by('-time1')
        else:
            chuan_qz=chuan_chaifen(chuan,'qz')
            chuan_qz.append(90000000)
            list1 =Caozuo.objects.filter(Q(cztype="发言",fystatus="正常有效"))
            list1 =list1.filter(fyfanwei__in=chuan_qz,uid0=yonghuid).order_by('-time1')
        
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time0','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(list1,safe=False)
        
#这是仅仅对“群动态”和“发言列表”的总数进行计数，其他例如“我”和“用户”动态的总数通过mongo进行计数
@csrf_exempt
def countqznei(request):
    data = json.loads(request.body)
    qzid = data.get('qzid')
    dongtaitype = data.get('dongtaitype')
    if dongtaitype=='群':
        list1 =Caozuo.objects.filter(            
            Q(cztype="分享",fystatus="正常有效")|
            Q(cztype="分享",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正在审核")|
            Q(cztype="发言",fystatus="正常有效"))
        list1 =list1.filter(fyfanwei=qzid).count()
    if dongtaitype=='发言列表':
        list1 =Caozuo.objects.filter(cztype="发言",fystatus="正常有效",uid0=qzid).count()
    return JsonResponse(list1,safe=False)
        
#这是在回复栏中顶和踩的操作
@csrf_exempt
def to_dingcai(request):
    data = json.loads(request.body)
    cztype = data.get('cztype')
    czid=data.get('czid')
    czid=int(czid)
    try:
        if cztype=="顶":
            cz1=Caozuo.objects.get(czid=czid)
            cz1.ding=cz1.ding+1
            cz1.save()
            b={"msg":0,"jishudingcai":cz1.ding}
            return JsonResponse(b)
        else:
            cz1=Caozuo.objects.get(czid=czid)
            cz1.cai=cz1.cai+1
            cz1.save()
            b={"msg":0,"jishudingcai":cz1.cai}
            return JsonResponse(b)
    except:
        b={"msg":1}
        return JsonResponse(b)

#这是“搜”的功能，k是指输入的搜索词
@csrf_exempt
def sou(request):
    data = json.loads(request.body)
    k  = data.get('k')
    userid  = data.get('userid')
    
    wenji1=Wenji.objects.filter(
        Q(wj_title__icontains=k,wj_status="正常有效",wj_fanwei=90000000)|
        Q(wj_remark__icontains=k,wj_status="正常有效",wj_fanwei=90000000)
        ).order_by('-wj_createtime')
    
    wenduan1=Wenduan.objects.filter(
        Q(wd_title__icontains=k,wd_status="正常有效",wd_fanwei=90000000,wd_type="知识百科")|
        Q(wd_content__icontains=k,wd_status="正常有效",wd_fanwei=90000000,wd_type="知识百科")).order_by('-wd_createtime')
    
    biaoqian1=Biaoqian.objects.filter(
        Q(bq_title__icontains=k,bq_status="正常有效",bq_fanwei=90000000)|
        Q(bq_remark__icontains=k,bq_status="正常有效",bq_fanwei=90000000)
        ).order_by('-bq_createtime')

    fayan1=Caozuo.objects.filter(
        cztype='发言',
        fy__icontains=k,
        fymi=0,
        fystatus="正常有效",
        fyfanwei=90000000).order_by('-time0')

    fuyan1=Caozuo.objects.filter(
        fy__icontains=k,
        fystatus='正常有效',
        fyfanwei=90000000,
        fymi=0).order_by('-time0')
    fuyan1=fuyan1.filter(
        Q(cztype='关联')|
        Q(cztype='评论')|
        Q(cztype='加入标签')|
        Q(cztype='分享'))

    wenji1 =serializers.serialize("json",wenji1)
    wenduan1 =serializers.serialize("json",wenduan1)
    biaoqian1 =serializers.serialize("json",biaoqian1)
    fayan1 =serializers.serialize("json",fayan1)
    fuyan1=serializers.serialize("json",fuyan1)
    Tongji.objects(tjid= userid).update_one(push__resouci=k)
    #add_to_set是添加但合并重复
    rr={
        "wenji1":wenji1,
        "wenduan1":wenduan1,
        "biaoqian1":biaoqian1,
        "fayan1":fayan1,
        "fuyan1":fuyan1
    }
    return JsonResponse(rr, safe=False)
    
    #这是在用户登录后，加载主页后，读取全站的宏观数据
@csrf_exempt
def showalldata(request):
    data = json.loads(request.body)
    k  = data.get('k')
    countall = Alljishu.objects.get(keyid=999)
    countall=countall.to_json()
    return JsonResponse(countall, safe=False)

#以下都是搜索页面自动给用户呈现的最新的知识点列表
@csrf_exempt
def xunhuan_wen2(request):
    data = json.loads(request.body)
    userid  = data.get('userid')
    userid=int(userid)
    cz1=Caozuo.objects.filter(cztype='提问',fystatus='正常有效',uid0=userid).values('czid')
    array1 = []
    for l1 in cz1:
        arr1 = l1['czid']
        array1.append(arr1)
    cz2=Caozuo.objects.filter(cztype='评论',fystatus='正常有效',id0__in=array1).order_by('-time1')
    cz3 =serializers.serialize("json",cz2,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(cz3, safe=False)

#以下都是搜索页面自动给用户呈现的最新的知识点列表
@csrf_exempt
def xunhuan_wen3(request):
    cz1=Caozuo.objects.filter(cztype='提问',fystatus='正常有效').order_by('-time1')
    cz2 =serializers.serialize("json",cz1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(cz2, safe=False)

#以下都是搜索页面自动给用户呈现的最新的知识点列表
@csrf_exempt
def xunhuans1(request):
    wenji1=Wenji.objects.filter(
        wj_status="正常有效",
        wj_fanwei=90000000).order_by('-wj_createtime')
    wenji1 =serializers.serialize("json",wenji1)
    return JsonResponse(wenji1, safe=False)
    
@csrf_exempt
def xunhuans2(request):
    wenduan1=Wenduan.objects.filter(
        wd_status="正常有效",
        wd_type="知识百科",
        wd_fanwei=90000000).order_by('-wd_createtime')[:10]
    wenduan1 =serializers.serialize("json",wenduan1)
    return JsonResponse(wenduan1, safe=False)
    
@csrf_exempt
def xunhuans3(request):
    biaoqian1=Biaoqian.objects.filter(
        bq_status="正常有效",
        bq_fanwei=90000000).order_by('-bq_createtime')[:10]
    biaoqian1=serializers.serialize("json",biaoqian1)
    return JsonResponse(biaoqian1, safe=False)
    
@csrf_exempt
def xunhuans5(request):
    fayan1=Caozuo.objects.filter(
        cztype="发言",
        fystatus="正常有效",
        fyfanwei=90000000,
        fymi=0).order_by('-time1')[:10]
    fayan1=serializers.serialize("json",fayan1)
    return JsonResponse(fayan1, safe=False) 

@csrf_exempt
def xunhuans6(request):
    fuyan1=Caozuo.objects.filter(
        Q(cztype="关联",fystatus="正常有效",fyfanwei=90000000,fymi=0)|
        Q(cztype="评论",fystatus="正常有效",fyfanwei=90000000,fymi=0)|
        Q(cztype="加入标签",fystatus="正常有效",fyfanwei=90000000,fymi=0)|
        Q(cztype="分享",fystatus="正常有效",fyfanwei=90000000,fymi=0)
        ).order_by('-time0')[:10]
    fuyan1=serializers.serialize("json",fuyan1)
    return JsonResponse(fuyan1, safe=False) 

#这是搜索页面显示用户曾经搜索的词汇
@csrf_exempt
def show_searchedword(request):
    data = json.loads(request.body)
    userid  = data.get('userid')
    tongji1 = Tongji.objects.get(tjid=userid)
    souci=tongji1.resouci
    return JsonResponse(souci, safe=False)

#以下是“增”的功能，用户新增各类知识点的功能
@csrf_exempt
def show_zengpage(request):
    data = json.loads(request.body)
    yonghu_id  = data.get('userid')
    yh_tongji = Tongji.objects.get(tjid=yonghu_id)
    list1={"yh_tongji":yh_tongji.to_json()}
    return JsonResponse(list1,safe=False)

@csrf_exempt
def zengwenji(request):
    data = json.loads(request.body)
    wj_title = data.get('wj_title')
    wj_createrid = data.get('userid')
    wj_creatername = data.get('username')
    wj_type = data.get('type_value')
    wj_remark = data.get('wj_shuoming')
    wj_diqu = data.get('wj_diqu')
    wj_hangye = data.get('wj_hangye')
    wj_type = data.get('wj_type')
    wj_fawenjigou = data.get('wj_fawenjigou')
    wj_born_time = data.get('wj_born_time')
    wj_dead_time = data.get('wj_dead_time')
    wj_fanwei = data.get('wj_fanwei')
    
    if wj_remark=="请输入备注或说明的内容。":
        wj_remark="无内容"
    if wj_remark=="":
        wj_remark="无内容"

    #这是给标题加一个书名号，首先要去掉原数据中的书名号
    wj_title=wj_title.strip().strip('《》「」')
    wj_title='《'+wj_title+'》'

    wenji1=Wenji(
        wj_title=wj_title,
        wj_remark=wj_remark,
        wj_createrid=wj_createrid,
        wj_manager=wj_createrid,
        wj_creatername=wj_creatername,
        wj_type=wj_type,
        wj_area=wj_diqu,
        wj_hangye=wj_hangye,
        wj_publisher=wj_fawenjigou,
        wj_borntime=wj_born_time,
        wj_deadtime=wj_dead_time,
        wj_createtime=timezone.now(),
        wj_fanwei=wj_fanwei
    )
    wenji1.save()
    if wenji1:
        tongji =Tongji(tjid=wenji1.wj_id)
        tongji1=tongji.save()
        #这是新增知识点，以备之后添加各种操作（分享等）
        yh_tongji = Tongji.objects.get(tjid=wj_createrid)
        yh_tongji.zengwenji=yh_tongji.zengwenji+1
        yh_tongji.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.wenji=alljishu.wenji+1
        alljishu.save()
        fanhuizhi={"msg": 1}
    else:
        fanhuizhi={"msg": 3}
    return JsonResponse(fanhuizhi, safe=False)
 
@csrf_exempt
def zengqunzu(request):
    data = json.loads(request.body)
    qz_title = data.get('qunzu_title')
    qz_createrid = data.get('userid')
    qz_creatername = data.get('username')
    qz_type = data.get('type_value')
    qz_remark = data.get('qunzu_shuoming')
    qz_kouling=data.get('kouling0')

    if qz_remark=='请输入此群组的介绍文字。':
        qz_remark='无'

    qz_title=qz_title.strip().strip('《》「」')
    qz_title='「'+qz_title+'」'

    qunzu1=Qunzu(
        qz_title=qz_title,
        qz_remark=qz_remark,
        qz_createrid=qz_createrid,
        qz_manager=qz_createrid,
        qz_creatername=qz_creatername,
        qz_type=qz_type,
        qz_kouling=qz_kouling,
        qz_createtime=timezone.now()
    )
    qunzu1.save()
    cz1=Caozuo(
        cztype =  '加入群组',
        id0 = qunzu1.qz_id,
        title0 = qz_title,
        type0 =  'qunzuye',
        uid0 = qz_createrid,
        uid1 = qz_createrid,
        uname = qz_creatername,
        time0 = datetime.now(),
        fy = '这是我本人创建的群组',
        fystatus='正常有效',
    )
    cz1.save()
    if qunzu1 and cz1:
        # 这是在tongji表里一个新增知识点的记录
        tongji =Tongji(tjid=qunzu1.qz_id,guanzhu=1)
        tongji1=tongji.save()
        yh_tongji = Tongji.objects.get(tjid=qz_createrid)
        yh_tongji.zengqunzu=yh_tongji.zengqunzu+1
        yh_tongji.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.qunzu=alljishu.qunzu+1
        alljishu.save()
        fanhuizhi={"msg": 1}
    else:
        fanhuizhi={"msg": 3}
    return JsonResponse(fanhuizhi, safe=False)

@csrf_exempt
def zengbiaoqian(request):
    data = json.loads(request.body)
    bq_title = data.get('bq_title')
    bq_fanwei = data.get('bq_fanwei')
    bq_creatername = data.get('username')
    bq_createrid = data.get('userid')
    bq_remark = data.get('bq_remark')

    if bq_remark=='请输入此标签的介绍文字。':
        bq_remark='无'

    bq_title=bq_title.strip().strip('《》「」')
    bq_title='「'+bq_title+'」'

    biaoqian1=Biaoqian(
        bq_title=bq_title,
        bq_remark=bq_remark,
        bq_createrid=bq_createrid,
        bq_manager=bq_createrid,
        bq_creatername=bq_creatername,
        bq_fanwei=bq_fanwei,
        bq_createtime=timezone.now()
    )
    biaoqian1.save()
    cz1=Caozuo(
        cztype = '关注',
        id0 = biaoqian1.bq_id,
        title0 = bq_title,
        type0 =  'biaoqianye',
        uid0 = bq_createrid,
        uid1 = bq_createrid,
        uname = bq_creatername,
        time0 = datetime.now(),
        time1 = datetime.now(),
        fy = '这是你本人创建的标签',
        fystatus='正常有效',
    )
    cz1.save()
    if cz1 and biaoqian1:
        tongji =Tongji(tjid=biaoqian1.bq_id,guanzhu=1)
        tongji1=tongji.save()
        yh_tongji = Tongji.objects.get(tjid=bq_createrid)
        yh_tongji.zengbiaoqian=yh_tongji.zengbiaoqian+1
        yh_tongji.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.biaoqian=alljishu.biaoqian+1
        alljishu.save()
        fanhuizhi={"msg": 1}
    else:
        fanhuizhi={"msg": 3}
    return JsonResponse(fanhuizhi, safe=False)
    
    #以下都是用户新增知识点的历史记录
@csrf_exempt
def xunhuan_zengwenji(request):
    data = json.loads(request.body)
    wj_createrid = data.get('userid')
    wj_list =Wenji.objects.filter(wj_createrid=wj_createrid).order_by('-wj_createtime')
    wj_list1=serializers.serialize("json",wj_list)
    return JsonResponse(wj_list1,safe=False)

@csrf_exempt
def xunhuan_zengbiaoqian(request):
    data = json.loads(request.body)
    bq_createrid = data.get('userid')
    bq_list =Biaoqian.objects.filter(bq_createrid=bq_createrid).order_by('-bq_createtime')
    bq_list1=serializers.serialize("json",bq_list)
    return JsonResponse(bq_list1,safe=False)

@csrf_exempt
def xunhuan_zengqunzu(request):
    data = json.loads(request.body)
    qz_createrid = data.get('userid')
    qz_list = Qunzu.objects.filter(qz_createrid=qz_createrid).order_by('-qz_createtime')
    qz_list1=serializers.serialize("json",qz_list)
    return JsonResponse(qz_list1,safe=False)
    
@csrf_exempt
def xunhuan_zengfayan(request):
    data = json.loads(request.body)
    fy_createrid = data.get('userid')
    fy_list =Caozuo.objects.filter(uid0=fy_createrid,cztype='发言').order_by('-time0')
    fy_list1=serializers.serialize("json",fy_list)
    return JsonResponse(fy_list1,safe=False)
    
    
@csrf_exempt
def xunhuan_zengwen(request):
    data = json.loads(request.body)
    wen_createrid = data.get('userid')
    wen_list =Caozuo.objects.filter(uid0=wen_createrid,cztype='提问').order_by('-time0')
    wen_list1=serializers.serialize("json",wen_list)
    return JsonResponse(wen_list1,safe=False)   
    
#以下是“增”的功能，用户新增各类知识点的功能
@csrf_exempt
def show_wenpage(request):
    data = json.loads(request.body)
    wen_createrid  = data.get('userid')
    mywen_list =Caozuo.objects.filter(uid0=wen_createrid,cztype='提问')
    allwen_count =Caozuo.objects.filter(cztype='提问',fystatus='正常有效').count()
    jieda_list =Caozuo.objects.filter(id0=wen_createrid,cztype='解答').order_by('-time0')
    lastwen=mywen_list.first()
    if lastwen ==None:
        lastwentime=0
    else:
        lastwentime=lastwen.time0
    mywen_count=mywen_list.count()
    jieda_count=jieda_list.count()
    jieda0=jieda_list.first()
    if jieda0 ==None:
        jieda1=0
    else:
        jieda1=jieda0.time0
    b={"mywen":mywen_count,"allwen":allwen_count,"jieda":jieda_count,"jieda1":jieda1,"lastwentime":lastwentime}
    return JsonResponse(b, safe=False)


@csrf_exempt
def xunhuan11(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    chuan = data.get('chuan')
    userid = int(userid)
    chuan_yh=chuan_chaifen(chuan,'yh')
    chuan_yh.append(userid)
    chuan_qz=chuan_chaifen(chuan,'qz')
    chuan_qz.append(90000000)
    # chuan_qz=list(set(chuan_qz)) set是去重复
    before_time = datetime.now() - timedelta(days=1)
    cz1 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        uid0__in=chuan_yh,
        fyfanwei__in=chuan_qz).order_by('-time1')
    cz1=cz1.filter(Q(cztype="分享")|Q(cztype="发言"))
    
    cz2 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        cztype="提问"
        ).order_by('-time1')
        
    cz0 = cz1 | cz2
    
    cz0 =serializers.serialize("json",cz0,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(cz0, safe=False)

@csrf_exempt
def count11(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    chuan = data.get('chuan')
    userid = int(userid)
    chuan_yh=chuan_chaifen(chuan,'yh')
    chuan_yh.append(userid)
    chuan_qz=chuan_chaifen(chuan,'qz')
    chuan_qz.append(90000000)
    before_time = datetime.now() - timedelta(days=1)
    cz1 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        uid0__in=chuan_yh,
        fyfanwei__in=chuan_qz).order_by('-time1')
    cz1=cz1.filter(Q(cztype="分享")|Q(cztype="发言")).count()
    
    cz2 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        cztype="提问"
        ).count()
    cz0=cz1+cz2
    return JsonResponse(cz0, safe=False)

@csrf_exempt
def xunhuan12(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    chuan = data.get('chuan')
    userid = int(userid)
    chuan_qz=chuan_chaifen(chuan,'qz')
    chuan_qz.append(90000000)
    chuan_zhi=chuan_chaifen(chuan,'zhi')
    before_time = datetime.now() - timedelta(days=1)
    cz1 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        id0__in=chuan_zhi,
        fyfanwei__in=chuan_qz).order_by('-time1')
    cz1=cz1.filter(Q(cztype="评论")|Q(cztype="关联")|Q(cztype="加入标签")|Q(cztype="标签里加入"))
    cz1 =serializers.serialize("json",cz1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(cz1, safe=False)
    
@csrf_exempt
def count12(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    chuan = data.get('chuan')
    userid = int(userid)
    chuan_qz=chuan_chaifen(chuan,'qz')
    chuan_qz.append(90000000)
    chuan_zhi=chuan_chaifen(chuan,'zhi')
    before_time = datetime.now() - timedelta(days=1)
    cz1 =Caozuo.objects.filter(
        time1__gt=before_time,
        fystatus='正常有效',
        id0__in=chuan_zhi,
        fyfanwei__in=chuan_qz).order_by('-time1')
    cz1=cz1.filter(Q(cztype="评论")|Q(cztype="关联")|Q(cztype="加入标签")|Q(cztype="标签里加入")).count()
    return JsonResponse(cz1, safe=False)

@csrf_exempt
def xunhuan13(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    userid = int(userid)
    list1 =Caozuo.objects.filter(
        Q(fystatus="正常有效",id0=userid,cztype="评价")
        |Q(fystatus="正常有效",uid0=userid,cztype="加入群组",id1__gt=90000000)).order_by('-time1')
    list1 =serializers.serialize("json",list1)
    return JsonResponse(list1, safe=False)
    
@csrf_exempt
def count13(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    userid = int(userid)
    list1 =Caozuo.objects.filter(
        Q(fystatus="正常有效",id0=userid,cztype="评价")
        |Q(fystatus="正常有效",uid0=userid,cztype="加入群组",id1__gt=90000000)).count()
    return JsonResponse(list1, safe=False)

@csrf_exempt
def xunhuan14(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    userid = int(userid)
    list1 =Caozuo.objects.filter(fystatus="已被拒绝",uid0=userid).order_by('-time1')
    array0=[]
    for item in list1:
        aaa = {
            'fyshen': item.fyshen[0:5],
            'time1': item.time1,
            'fystatus':item.fystatus,
            'id0':item.id0,
            'title0':item.title0,
        }
        array0.append(aaa)
    return JsonResponse(array0, safe=False)
    
@csrf_exempt
def count14(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    userid = int(userid)
    list1 =Caozuo.objects.filter(fystatus="已被拒绝",uid0=userid).count()
    return JsonResponse(list1, safe=False)

@csrf_exempt
def xunhuan2x(request):
    data = json.loads(request.body)
    userid = int(data.get('userid'))
    zoneid = data.get('zoneid')
    cztype=''
    type0=''
    
    if zoneid=='21':
        cztype="关注"
        type0="biaoqianye"
    if zoneid=='22':
        cztype="关注"
        type0="wenjiye"
    if zoneid=='23':
        cztype="关注"
        type0="wenduanye"
    if zoneid=='24':
        cztype="关注"
        type0="fayanye"
    if zoneid=='27':
        cztype="关注"
        type0="yonghuye"
    if zoneid=='32':
        cztype="关注"
        type0="yonghuye"
    if zoneid=='35':
        cztype="加入群组"
        type0="qunzuye"
        
    list1 =Caozuo.objects.filter(
        cztype=cztype,
        type0=type0,
        uid0=userid).order_by('-time1')
    list1=list1.filter(Q(fystatus='正常有效')|Q(fystatus='正在审核'))
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    return JsonResponse(list1,safe=False)
    
    #这就修改用户关注知识点的附言
@csrf_exempt
def edit_fuyan(request):
    data = json.loads(request.body)
    fuid  = data.get('fuid')
    fuyan  = data.get('fuyan')
    try:
        Caozuo.objects.filter(czid=fuid).update(fy=fuyan)
        b={"changed_ok":0}
        return JsonResponse(b, safe=False)
    except:
        b={"changed_ok":2}
        return JsonResponse(b, safe=False)
    return JsonResponse(b)


@csrf_exempt
def xunhuan3x(request):
    data = json.loads(request.body)
    userid = data.get('userid')
    chuan = data.get('chuan')
    zoneid = data.get('zoneid')
    if zoneid=='31':
        yonghu1=Yonghu.objects.filter(yonghu_type='普通用户',yonghu_status='正常有效').order_by('-yonghu_fresh')[:10]
        list3x =serializers.serialize("json",yonghu1)
    if zoneid=='36':
        yonghu1=Yonghu.objects.filter(yonghu_type='人物名片').order_by('-yonghu_fresh')
        list3x =serializers.serialize("json",yonghu1)
    if zoneid=='37':
        yonghu1=Yonghu.objects.filter(yonghu_type='工团组织').order_by('-yonghu_fresh')
        list3x =serializers.serialize("json",yonghu1)
    if zoneid=='32':
        uidlist=chuan_chaifen(chuan,'yh')
        yonghu1=Yonghu.objects.filter(yonghu_id__in=uidlist).order_by('-yonghu_fresh')
        list3x =serializers.serialize("json",yonghu1)
    if zoneid=='33':
        userid = int(userid)
        list1 =Caozuo.objects.filter(cztype="关注",uid0=userid)
        list1=list1.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核")).values('id0')
        array1 = []
        for l1 in list1:
            arr1 = l1['id0']
            array1.append(arr1)
        yonghu1=Yonghu.objects.filter(yonghu_id__in = array1).order_by('-yonghu_fresh')
        list3x=serializers.serialize("json",yonghu1)
    if zoneid=='34':
        qunzu1=Qunzu.objects.filter(qz_status='正常有效').order_by('-qz_createtime')
        list3x =serializers.serialize("json",qunzu1)
    if zoneid=='35':
        qzlist=chuan_chaifen(chuan,'qz')
        qunzu1=Qunzu.objects.filter(qz_id__in=qzlist).order_by('-qz_createtime')
        list3x =serializers.serialize("json",qunzu1)
    return JsonResponse(list3x, safe=False)


@csrf_exempt
def xunhuan31sou(request):
    data = json.loads(request.body)
    kkk = data.get('kkk')
    yonghu1=Yonghu.objects.filter(yonghu_type='普通用户',yonghu_name__icontains=kkk).order_by('-yonghu_borntime')
    yonghu1 =serializers.serialize("json",yonghu1)
    return JsonResponse(yonghu1, safe=False)
    
@csrf_exempt
def xunhuan34_sou(request):
    data = json.loads(request.body)
    k  = data.get('k')
    qunzu1=Qunzu.objects.filter(qz_title__icontains=k).order_by('-qz_createtime')
    qunzu1 =serializers.serialize("json",qunzu1)
    return JsonResponse(qunzu1, safe=False)

@csrf_exempt
def xunhuanpl(request):
    data = json.loads(request.body)
    id0 = data.get('zhid')
    list1 =Caozuo.objects.filter(cztype="评论",id0=id0).order_by('-time1')
    list1 =list1.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核"))
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time1','ding','cai','hui','fyhui','fujianshu'))
    b={'list':list1}
    return JsonResponse(b,safe=False)
    
#在新增页面删除新增的纪录,这里各个知识点有区别，其中群组删除时，要同时删除yonghuaciton表。
@csrf_exempt
def shanchu(request):
    data = json.loads(request.body)
    zhid  = data.get('zhid')
    leixing  = data.get('leixing')
    userid= data.get('userid')

    if leixing=="8":
        Qunzu.objects.filter(qz_id=zhid).update(qz_status="失效已删")
        Caozuo.objects.filter(
            id0=zhid,
            cztype='关注',
            uid0=userid).update(fystatus="失效已删")
        # tongji =Tongji.objects.get(tjid=userid)
        # tongji.zengqunzu=tongji.zengqunzu-1
        # tongji.save()
    if leixing=="1":
        Biaoqian.objects.filter(bq_id=zhid).update(bq_status="失效已删")
        Caozuo.objects.filter(
            id0=zhid,
            cztype='加入标签',
            uid0=userid).update(fystatus="失效已删")
        # tongji =Tongji.objects.get(tjid=userid)
        # tongji.zengbiaoqian=tongji.zengbiaoqian-1
        # tongji.save()
    if leixing=="2":
        Wenji.objects.filter(wj_id=zhid).update(wj_status="失效已删")
        # tongji =Tongji.objects.get(tjid=userid)
        # tongji.zengwenji=tongji.zengwenji-1
        # tongji.save()
    if leixing=="21":
        wenduan1=Wenduan.objects.get(wd_id=zhid)
        wenduan1.wd_status="失效已删"
        wenduan1.save()
        # wenji1=Wenji.objects.get(wj_id=wenduan1.wj_id)
        # wenji1.wj_wdshu=wenji1.wj_wdshu-1
        # wenji1.save()
        # tongji =Tongji.objects.get(tjid=wenduan1.wj_id)
        # tongji.neihan=tongji.neihan-1
        # tongji.save()
    if leixing=="3":
        Caozuo.objects.filter(czid=zhid).update(fystatus="失效已删")
        
    b={"changed_ok":0}
    return JsonResponse(b)
        
#这些都是用于登陆和注册相关的功能
#这是用户在注册的时候，检测用户名称是否已经存在，如果存在，返回报错
@csrf_exempt
def zhuce_name_exist(request):
    data = json.loads(request.body)
    username  = data.get('username')
    # username = request.POST.get('username', None)
    name_existed = Yonghu.objects.filter(yonghu_name=username)
    if name_existed:
        r_existed = {'name_existed': 1}
        response = JsonResponse(r_existed)
        return response
    else:
        r_existed = {'name_existed': 0}
        response = JsonResponse(r_existed)
        return response

@csrf_exempt
def denglu(request):
    data = json.loads(request.body)
    yonghu_name  = data.get('username')
    yonghu_pswd = data.get('userpswd')
    r_namenotexist = {'dengluok': 1,'msg': '用户名不存在！'}
    r_pswdwrong = {'dengluok': 2,'msg': '用户密码错误！'}
    r_statuswrong = {'dengluok': 3,'msg': '用户正在审核！'}
    yonghu1 = Yonghu.objects.get(yonghu_name=yonghu_name)
    if yonghu1:
        if check_password(yonghu_pswd, yonghu1.yonghu_pswd)==True:
            if yonghu1.yonghu_status!='正常有效':
                response = JsonResponse(r_statuswrong)
                return response
            else:
                # request.session['count'] = 1
                # fymm=Caozuo.objects.filter(cztype='发言密码',uid0=yonghu1.yonghu_id).order_by('-time0')[0]
                fymm=Caozuo.objects.filter(cztype='发言密码',uid0=yonghu1.yonghu_id).last()
                fymm=fymm.id1
                
                 # 以下是调取用户最后一次提问的时间
                mywen_list =Caozuo.objects.filter(uid0=yonghu1.yonghu_id,cztype='提问')
                lastwen=mywen_list.first()
                if lastwen ==None:
                    lastwentime="2020-01-01T00:00:00"
                else:
                    lastwentime=lastwen.time1
                    
                r_ok = {
                    'dengluok': 0,
                    "yonghu_name":yonghu1.yonghu_name,
                    "yonghu_id":yonghu1.yonghu_id,
                    "yonghu_type":yonghu1.yonghu_type,
                    "chuan":genxin_idchuan(yonghu1.yonghu_id),
                    "fymm":fymm,
                    "lastwentime":lastwentime
                }
                response = JsonResponse(r_ok)
                return response
        else:
            response = JsonResponse(r_pswdwrong)
            return response
    else:
        response = JsonResponse(r_namenotexist)
        return response

#这是用户登录后读取用户本人的一些数据
@csrf_exempt
def showmydata(request):
    data = json.loads(request.body)
    yonghuid = data.get('yonghuid')
    yonghuid=int(yonghuid)
    yh_tongji = Tongji.objects.get(tjid=yonghuid)
    tongji_wj=yh_tongji.to_json()
    return JsonResponse(tongji_wj, safe=False)

@csrf_exempt
def reset_denglumima(request):
    data = json.loads(request.body)
    userid  = data.get('userid')
    dlmm0 = data.get('dlmm0')
    dlmm0=make_password(dlmm0,"******")
    try:
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_pswd=dlmm0)
        r_ok = {'resetmm': 0}
        response = JsonResponse(r_ok)
        return response
    except:
        r_ok = {'resetmm': 1}
        response = JsonResponse(r_ok)
        return response
        
#注册用户后自动生成：关注小知，新手，使用说明，发言密码的初始密码
@csrf_exempt
def zhuce(request):
    data = json.loads(request.body)
    yonghu_name  = data.get('username')
    yonghu_remark  = data.get('remark')
    yonghu_pswd = data.get('userpswd')
    yonghu_pswd=make_password(yonghu_pswd,"******")
    # yonghu_name = request.POST.get('username', None)
    yonghu1 =Yonghu(
        yonghu_name=yonghu_name,
        yonghu_remark=yonghu_remark,
        yonghu_pswd=yonghu_pswd,
        yonghu_borntime=timezone.now())
    yonghu1.save()
    u_id=yonghu1.yonghu_id
    u_name=yonghu_name
    cz0=Caozuo(cztype ='加入群组',
        fy = '这是用户首次注册后自动加入的群组',
        fyshen='这是用户首次注册后自动加入的群组',
        fymi = 0, fystatus='正常有效',
        id0 = 80000001, title0 = '新用户须知群',type0 ='qunzuye',
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz0.save()
    cz1=Caozuo(cztype ='关注',
        fy = '这是网站管理员。有问题，问小知。',
        fyshen='这是网站管理员。有问题，问小知。',
        fymi = 0, fystatus='正常有效',
        id0 = 90000001, title0 = '小知',type0 ='yonghuye',
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz1.save()
    cz2=Caozuo(cztype ='公告',
        fy = '这个人什么都没写',
        fyshen='这个人什么都没写',
        fymi = 0, fystatus='正常有效',
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz2.save()
    cz3=Caozuo(cztype ='发言密码',
        fy = '初始密码八个1',
        fyshen='初始密码八个1',
        fymi = 0, fystatus='正常有效',
        id0=u_id,id1=11111111,
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz3.save()
    cz4=Caozuo(cztype ='关注',
        fy = '这是新手的须知标签。',
        fyshen='这是新手的须知标签。',
        fymi = 0, fystatus='正常有效',
        id0 = 30000001, title0 = '新手须知',type0 ='biaoqianye',
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz4.save()
    cz5=Caozuo(cztype ='关注',
        fy = '这是网站功能使用手册。',
        fyshen='这是网站功能使用手册。',
        fymi = 0, fystatus='正常有效',
        id0 = 10000001, title0 = '《网站功能使用手册》',type0 ='wenjiye',
        uid0 = u_id,uid1 = u_id,uname = u_name,
        time0 = datetime.now(),time1 = datetime.now(),
        )
    cz5.save()
    # alljishu = Alljishu.objects.get(keyid=999)
    # alljishu.yonghu=alljishu.yonghu+1
    # alljishu.save()
    #这是用户在tongji中创建一条用户记录
    tongji =Tongji(tjid=yonghu1.yonghu_id,updatetime=datetime.now())
    tongji1=tongji.save()
    if yonghu1:
        r_ok = {
            'zhuceok': 0,
            'yonghu_id':yonghu1.yonghu_id,
            'yonghu_name':yonghu1.yonghu_name,
            "yonghu_type":yonghu1.yonghu_type}
        return JsonResponse(r_ok, safe=False)
    else:
        r_mima = {'zhuceok': 1,'msg': '密码错误！'}
        return JsonResponse(r_mima, safe=False)

#这是显示用户公告
@csrf_exempt
def show_mygonggao(request):
    data = json.loads(request.body)
    userid  = data.get('userid')
    gg_list1=Caozuo.objects.filter(cztype='公告',uid0=userid).last()
    list1={
        "gg":gg_list1.fy,
        "gg_mizi":gg_list1.fymi,
        "gg_time":gg_list1.time1,
        "gg_status":gg_list1.fystatus,
    }
    return JsonResponse(list1,safe=False)

@csrf_exempt
def show_mypage(request):
    data = json.loads(request.body)
    yonghu_id  = data.get('userid')
    yh_list = Yonghu.objects.get(yonghu_id=yonghu_id)
    yh_tongji = Tongji.objects.get(tjid=yonghu_id)
    alljishu = Alljishu.objects.get(keyid=999)
    list1={
        "yonghu_name":yh_list.yonghu_name,
        "yonghu_id":yh_list.yonghu_id,
        "yonghu_remark":yh_list.yonghu_remark,
        "yonghu_type":yh_list.yonghu_type,
        "yonghu_area":yh_list.yonghu_area,
        "yonghu_job":yh_list.yonghu_job,
        "yonghu_contact":yh_list.yonghu_contact,
        "yonghu_hobby":yh_list.yonghu_hobby,
        "yonghu_borntime":yh_list.yonghu_borntime,
        "yonghu_touxiang":yh_list.yonghu_touxiang,
        "yonghu_born":yh_list.yonghu_born,
        "yonghu_life":yh_list.yonghu_life,
        # 这里需要用yh_tongji.updatetime来赋值，因为通过to_json的形式是会产生一个时间戳
        "yonghu_updatetime":yh_tongji.updatetime,
        "yh_tongji":yh_tongji.to_json(),
        "alljishu":alljishu.to_json(),
    }
    #这是更新用的上次登陆时间，主要不能在登陆的时候更新，而是在用户页面显示之后再显示。这样用户登陆之后看见的是上次登陆的时间，而不是本次登陆时间。
    tongji =Tongji.objects.get(tjid=yh_list.yonghu_id)
    tongji.updatetime=timezone.now()
    tongji.save()
    return JsonResponse(list1,safe=False)

@csrf_exempt
def edit_mypage(request):
    # 这是在41版面修改用户信息的功能,首先是要接收更改信息的类型，判断后对相应的字段进行修改。
    # 这里用loads来接收，接收的zhi_type为字符串格式，
    data = json.loads(request.body)
    userid  = data.get('userid')
    zhi  = data.get('zhi')
    zhi_type  = data.get('zhi_type')
    shen_yn  = data.get('shen_yn')
    if zhi_type=="1":
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_job=zhi)
    if zhi_type=="2":
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_area=zhi)
    if zhi_type=="3":
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_contact=zhi)
    if zhi_type=="4":
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_hobby=zhi)
    if zhi_type=="5":
        # yonghu1=Yonghu(yonghu_id=userid)
        # yonghu1.yonghu_remark=zhi
        # yonghu1.save()
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_remark=zhi)
    if zhi_type=="6":
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_life=zhi)
    if shen_yn is not 1:
        Yonghu.objects.filter(yonghu_id=userid).update(yonghu_fresh=timezone.now())
    b={"changed_ok":0}
    return JsonResponse(b)

#以下是调取各种页面的数据
# 调取用户信息（用户姓名，用户被关注数据，用户头像）的功能。
@csrf_exempt
def show_yonghuye(request):
    data = json.loads(request.body)
    yonghu_id  = data.get('userid')
    kkk  = data.get('kkk')
    yh_list = Yonghu.objects.get(yonghu_id=yonghu_id)
    yh_tongji = Tongji.objects.get(tjid=yonghu_id)
    if kkk==True:#这个kkk是用来判断是来自于mypage还是yonghuye的点击，如果来自本人则不增
        yh_tongji.dianji=yh_tongji.dianji+1
        yh_tongji.save()
    list1={
        "yonghu_name":yh_list.yonghu_name,
        "yonghu_id":yh_list.yonghu_id,
        "yonghu_remark":yh_list.yonghu_remark,
        "yonghu_type":yh_list.yonghu_type,
        "yonghu_area":yh_list.yonghu_area,
        "yonghu_job":yh_list.yonghu_job,
        "yonghu_contact":yh_list.yonghu_contact,
        "yonghu_hobby":yh_list.yonghu_hobby,
        "yonghu_borntime":yh_list.yonghu_borntime,
        "yonghu_touxiang":yh_list.yonghu_touxiang,
        "yonghu_born":yh_list.yonghu_born,
        "yonghu_life":yh_list.yonghu_life,
        "yonghu_updatetime":yh_tongji.updatetime,
        "yh_tongji":yh_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)    
    
@csrf_exempt
def show_qunzuye(request):
    data = json.loads(request.body)
    qunzu_id  = data.get('qunzu_id')
    qz_list = Qunzu.objects.get(qz_id=qunzu_id)
    qz_tongji = Tongji.objects.get(tjid=qunzu_id)
    qz_tongji.dianji=qz_tongji.dianji+1
    qz_tongji.save()
    list1={
        "qz_title":qz_list.qz_title,
        "qz_id":qz_list.qz_id,
        "qz_remark":qz_list.qz_remark,
        "qz_join":qz_list.qz_join,
        "qz_type":qz_list.qz_type,
        "qz_status":qz_list.qz_status,
        "qz_manager" :qz_list.qz_manager,
        "qz_kouling" :qz_list.qz_kouling,
        "qz_tongji":qz_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)
    
    #这是用于显示qunzuye中群组包含的用户列表
@csrf_exempt
def xunhuan_zuyuan(request):
    data = json.loads(request.body)
    manager_yn = data.get('manager_yn')
    qzid=int(data.get('qzid'))
    if manager_yn==True:
        list1 =Caozuo.objects.filter(cztype="加入群组",id0=qzid).order_by('-time1')
    if manager_yn==False:
        list1 =Caozuo.objects.filter(cztype="加入群组",id0=qzid,fystatus='正常有效').order_by('-time1')
    list1=serializers.serialize("json",list1)
    return JsonResponse(list1,safe=False)
    
@csrf_exempt
def count_zuyuan(request):
    data = json.loads(request.body)
    manager_yn = data.get('manager_yn')
    qzid=int(data.get('qzid'))
    if manager_yn==True:
        list1 =Caozuo.objects.filter(cztype="加入群组",id0=qzid).count()
    if manager_yn==False:
        list1 =Caozuo.objects.filter(cztype="加入群组",id0=qzid,fystatus='正常有效').count()
    return JsonResponse(list1,safe=False)




@csrf_exempt
def show_wenjiye(request):
    data = json.loads(request.body)
    wenji_id  = data.get('wj_id')
    wj_list = Wenji.objects.get(wj_id=wenji_id)
    wj_tongji = Tongji.objects.get(tjid=wenji_id)
    wj_tongji.dianji=wj_tongji.dianji+1
    wj_tongji.save()

    list1={
        "wj_id":wj_list.wj_id,
        "wj_title":wj_list.wj_title,
        "wj_remark":wj_list.wj_remark,
        "wj_borntime":wj_list.wj_borntime,
        "wj_deadtime":wj_list.wj_deadtime,
        "wj_status":wj_list.wj_status,
        "wj_type":wj_list.wj_type,
        "wj_fanwei" :wj_list.wj_fanwei, 
        "wj_area" :wj_list.wj_area,
        "wj_hangye" :wj_list.wj_hangye,
        "wj_publisher" :wj_list.wj_publisher,
        "wj_createrid" :wj_list.wj_createrid,
        "wj_creatername" :wj_list.wj_creatername,
        "wj_manager" :wj_list.wj_manager,
        "wj_wdlist":wj_list.wj_wdlist,
        "wj_wdshu":wj_list.wj_wdshu,
        "wj_yuanwen":wj_list.wj_yuanwen,
        "fujianshu":wj_list.fu,
        "wj_tongji":wj_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)

@csrf_exempt
def show_wenduanye(request):
    data = json.loads(request.body)
    wenduan_id  = data.get('wenduan_id')

    wd_list = Wenduan.objects.get(wd_id=wenduan_id)
    wj_list = Wenji.objects.get(wj_id=wd_list.wj_id)
    
    wd_tongji = Tongji.objects.get(tjid=wenduan_id)
    wd_tongji.dianji=wd_tongji.dianji+1
    wd_tongji.save()

    list1={
        "wj_id":wj_list.wj_id,
        "wj_title":wj_list.wj_title,
        "wj_borntime":wj_list.wj_borntime,
        "wj_deadtime":wj_list.wj_deadtime,
        "wj_status":wj_list.wj_status,
        "wj_type":wj_list.wj_type,
        "wj_fanwei" :wj_list.wj_fanwei, 
        "wj_area" :wj_list.wj_area,
        "wj_hangye" :wj_list.wj_hangye,
        "wj_publisher" :wj_list.wj_publisher,
        "wj_manager" :wj_list.wj_manager,
        "wj_wdlist":wj_list.wj_wdlist,
        "wj_wdshu":wj_list.wj_wdshu,
        
        "wd_id":wd_list.wd_id,
        "wd_title":wd_list.wd_title,
        "wd_status":wd_list.wd_status,
        "wd_type":wd_list.wd_type,
        "wd_fanwei":wd_list.wd_fanwei,
        "wd_manager" :wd_list.wd_manager,
        "wd_content" :wd_list.wd_content,
        "wd_xuhao" :wd_list.wj_xuhao,
        
        "wd_tongji":wd_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)

#这是显示wenjiye和wenduanye中该文集下段落列表
@csrf_exempt
def xunhuan_duanluo(request):
    data = json.loads(request.body)
    wj_id  = data.get('wj_id')
    sss  = data.get('sss')
    wenduan1 =Wenduan.objects.filter(wj_id=wj_id)
    if sss==1:
        wenduan1 =wenduan1.order_by('-wd_createtime')
    wenduan1 =serializers.serialize("json",wenduan1)
    return JsonResponse(wenduan1, safe=False)

#这是显示wenjiye和wenduanye中显示上一段和下一段
@csrf_exempt
def show_shangduan(request):
    data = json.loads(request.body)
    xuhao  = data.get('xuhao')
    wjid  = data.get('wj_id')
    wenduan1=Wenduan.objects.filter(
        Q(wj_xuhao__lt=xuhao)&
        Q(wj_id=wjid)&
        Q(wd_status="正常有效")).order_by('-wj_xuhao')
    try:
        rr=wenduan1[0].wd_id
    except:
        rr="null"
    return JsonResponse(rr, safe=False)
    
@csrf_exempt
def show_xiaduan(request):
    data = json.loads(request.body)
    xuhao  = data.get('xuhao')
    wjid  = data.get('wj_id')
    wenduan1=Wenduan.objects.filter(
        Q(wj_xuhao__gt=xuhao)&
        Q(wj_id=wjid)&
        Q(wd_status="正常有效")).order_by('wj_xuhao')
    try:
        rr=wenduan1[0].wd_id
    except:
        rr="null"
    return JsonResponse(rr, safe=False)

@csrf_exempt
def show_biaoqianye(request):
    data = json.loads(request.body)
    biaoqian_id  = data.get('biaoqian_id')
    bq_list = Biaoqian.objects.get(bq_id=biaoqian_id)
    bq_tongji = Tongji.objects.get(tjid=biaoqian_id)
    bq_tongji.dianji=bq_tongji.dianji+1
    bq_tongji.save()
    list1={
        "bq_title":bq_list.bq_title,
        "bq_id":bq_list.bq_id,
        "bq_remark":bq_list.bq_remark,
        "bq_type":bq_list.bq_type,
        "bq_status":bq_list.bq_status,
        "bq_fanwei":bq_list.bq_fanwei,
        "bq_manager":bq_list.bq_manager,
        "bq_tongji":bq_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)

@csrf_exempt
def show_fayanye(request):
    data = json.loads(request.body)
    fayan_id  = data.get('fayan_id')
    fy_list = Caozuo.objects.get(czid=fayan_id,type0='fayanye')
    fy_tongji = Tongji.objects.get(tjid=fayan_id)
    fy_tongji.dianji=fy_tongji.dianji+1
    fy_tongji.save()
    # 这里要判断一下，如果是失效等情况，则不能输出全部字段。
    list1={
        "fy_content":fy_list.fy,
        "fy_id":fy_list.czid,
        "wen_yn":fy_list.cztype,
        "fy_type":fy_list.type0,
        "fy_fytype":fy_list.fytype,
        "fy_status":fy_list.fystatus,
        "fy_fanwei":fy_list.fyfanwei,
        "fy_att":fy_list.fyatt,
        "fy_fu":fy_list.fujianshu,
        "fy_createrid":fy_list.uid0,
        "fy_creatername":fy_list.uname,
        "fy_createtime":fy_list.time0,
        
        "fy_zishu":fy_list.fymi,
        "fy_tongji":fy_tongji.to_json()
    }
    return JsonResponse(list1,safe=False)

    #这是调取这个知识点下属的附件id号
@csrf_exempt
def show_futujian(request):
    data = json.loads(request.body)
    zhid  = data.get('zhid')
    fu_list = Fujian.objects.filter(item_id=zhid,fu_status="正常有效")
    fu_list1=serializers.serialize("json",fu_list)
    return JsonResponse(fu_list1,safe=False)

@csrf_exempt
def uploadfu(request):
    zhid = request.POST.get('id', None)
    leixing  = request.POST.get('leixing', None)
    # createrid = request.POST.get('createrid', None)
    if leixing=="1":
        biaoqian1=Biaoqian.objects.get(bq_id=zhid)
        biaoqian1.fu=biaoqian1.fu+1
        biaoqian1.save()
    if leixing=="2":
        wenji1=Wenji.objects.get(wj_id=zhid)
        wenji1.fu=wenji1.fu+1
        wenji1.save()
    if leixing=="21":
        wenduan1=Wenduan.objects.get(wd_id=zhid)
        wenduan1.fu=wenduan1.fu+1
        wenduan1.save()
    if leixing=="3":
        fayan1=Caozuo.objects.get(czid=zhid)
        fayan1.fujianshu=fayan1.fujianshu+1
        fayan1.save()
    if leixing=="8":
        qunzu1=Qunzu.objects.get(qz_id=zhid)
        qunzu1.fu=qunzu1.fu+1
        qunzu1.save()
    filess = request.FILES.getlist("zhifujian")
    for f in filess:
        f_name, f_ext = os.path.splitext(f.name)
        fu1=Fujian(
            fu_type=f_ext,
            fu_title=f_name,
            item_id=zhid,
            fu_createtime=timezone.now()
            )
        fu1.save()
        fu_id=str(fu1.fu_id)
        upload1(f,"fujian/"+fu_id+f_ext)
    fanhuizhi={"ok_id": 0}
    return JsonResponse(fanhuizhi, safe=False)

#用户上传头像
@csrf_exempt
def shangchuan1(request):
    zhid = request.POST.get('user_id', None)
    mytouxiang = request.FILES.get("touxiang",None) 
    if not mytouxiang:
        b=0
        return JsonResponse(b, safe=False)
    else:
        zhid=str(zhid)
        upload1(mytouxiang,"touxiang/"+zhid+".jpg")
        Yonghu.objects.filter(yonghu_id=zhid).update(
            yonghu_touxiang=1,yonghu_fresh=timezone.now())
        b=1
        return JsonResponse(b, safe=False)
        
# 上传原文的功能        
@csrf_exempt
def shangchuan_yuanwen(request):
    zhid = request.POST.get('id', None)
    yuanwen = request.FILES.get("yuanwen",None) 
    try:
        wenji1=Wenji.objects.get(wj_id=zhid)
        wenji1.wj_yuanwen=1
        wenji1.save()
        zhid=str(zhid)
        upload1(yuanwen,"yuanwen1/"+zhid+".doc")
        b=1
        return JsonResponse(b, safe=False)   
    except:
        b=0
        return JsonResponse(b, safe=False)       
        
@csrf_exempt
def listmyqunzu(request):
    data = json.loads(request.body)
    uid = data.get('userid')
    cztype = data.get('cztype')
    qz_list = Caozuo.objects.filter(
        uid0=uid,cztype="加入群组",type0="qunzuye",fystatus="正常有效").order_by('-time0')
    if cztype == '分享':
        array0 = [{'qz_id':90000000,'qz_title':"--所有人--"}]
    else:
        array0 = [{'qz_id':80000000,'qz_title':"--仅本人--"},{'qz_id':90000000,'qz_title':"--所有人--"}]
    for item in qz_list:
        aaa = { 'qz_id': item.id0,'qz_title': item.title0}
        array0.append(aaa)
    return JsonResponse(array0,safe=False)

@csrf_exempt
def listmybiaoqian(request):
    data = json.loads(request.body)
    uid = data.get('userid')
    bq_list = Caozuo.objects.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核"))
    bq_list = bq_list.filter(uid0=uid,cztype="关注",type0="biaoqianye").order_by('-time0')
    array0 = []
    for item in bq_list:
        aaa = { 'bq_id': item.id0,'bq_title': item.title0,'bq_fanwei':item.fyfanwei}
        array0.append(aaa)
    return JsonResponse(array0,safe=False)

#django中的request.POST只能取到Content-Type(请求头)为application/x-www-form-urlencoded(form表单默认格式)的数据，如果请求头为application/json(json格式)，multipart/form-data(文件)等格式无法取到，只有在request.body里面能取到原生的数据。当发送过来的是JSON数据是，request.POST取到的数据是空的，这时只有用request.body取，再反序列化才能使用。
@csrf_exempt
def shangchuan999(request):
    wj_id = request.POST.get('wj_id', None)
    wj_title = request.POST.get('wj_title', None)
    wd_manager = request.POST.get('wd_manager', None)
    wd_creatername = request.POST.get('wd_creatername', None)
    wd_createrid = request.POST.get('wd_createrid', None)
    wd_type = request.POST.get('wd_type', None)
    duanlist = request.FILES.get("duanlist") 
    # file = xlrd.open_workbook(duanlist)
    file1 = xlrd.open_workbook(file_contents=duanlist.read())
    sheet = file1.sheets()[0]#获取第一个sheet
#     # nrows = sheet.nrows获取行数
#     # ncols = sheet.ncols获取列数
    for rrr in range(sheet.nrows):
        wenduan999 = Wenduan(
        wd_title=sheet.cell(rrr,0).value,
        wd_content=sheet.cell(rrr,1).value,
        wd_type=wd_type,
        wd_creatername=wd_creatername,
        wd_createrid=wd_createrid,
        wd_manager =wd_manager,
        wd_createtime = timezone.now(),
        wj_id=wj_id,
        wj_title=wj_title,
        wj_xuhao=sheet.cell(rrr,2).value
        )
        wenduan999.save()
        tongji =Tongji(tjid=wenduan999.wd_id)
        tongji1=tongji.save()

    wj0 = Wenji.objects.get(wj_id=wj_id)
    wj0.wj_wdshu=wj0.wj_wdshu+sheet.nrows
    wj0.save()
    alljishu = Alljishu.objects.get(keyid=999)
    alljishu.wenduan=alljishu.wenduan+sheet.nrows
    alljishu.save()
    
    rr=999
    return JsonResponse(rr, safe=False) 


#这是新增历史人物名片
@csrf_exempt
def zenginfo1(request):
    data = json.loads(request.body)
    try:
        yonghu1=Yonghu(
            yonghu_name= data.get('yonghu_name'),
        	yonghu_pswd= make_password(data.get('yonghu_pswd'),"******"),
        	yonghu_status= '正常有效',
        	yonghu_type= '人物名片',
        	yonghu_area= data.get('yonghu_area'),
        	yonghu_job= data.get('yonghu_job'),
        	yonghu_remark= data.get('yonghu_remark'),
        	yonghu_born= data.get('yonghu_borntime'),
        	yonghu_life= data.get('yonghu_life'),
            )
        yonghu1.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.yonghu1=alljishu.yonghu1+1
        alljishu.save()
        tongji =Tongji(tjid=yonghu1.yonghu_id,updatetime=datetime.now())
        tongji1=tongji.save()
        cz2=Caozuo(cztype ='公告',
            fy = '这个人什么都没写',
            fyshen='这个人什么都没写',
            fymi = 0, fystatus='正常有效',
            uid0 = yonghu1.yonghu_id,uid1 = yonghu1.yonghu_id,uname = yonghu1.yonghu_name,
            time0 = datetime.now(),time1 = datetime.now(),
        )
        cz2.save()
        cz3=Caozuo(cztype ='发言密码',
            fy = '初始密码八个1',
            fyshen='初始密码八个1',
            fymi = 0, fystatus='正常有效',
            id0=yonghu1.yonghu_id,id1=11111111,
            uid0 = yonghu1.yonghu_id,uid1 = yonghu1.yonghu_id,uname = yonghu1.yonghu_name,
            time0 = datetime.now(),time1 = datetime.now(),
        )
        cz3.save()
        b={"okmsg":0}
    except:
        b={"okmsg":1}
    return JsonResponse(b, safe=False)

#这是新增工团组织
@csrf_exempt
def zenginfo2(request):
    data = json.loads(request.body)
    try:
        yonghu1=Yonghu(
            yonghu_name= data.get('yonghu_name'),
        	yonghu_pswd= make_password(data.get('yonghu_pswd'),"******"),
        	yonghu_status= '正常有效',
        	yonghu_type= '工团组织',
        	yonghu_area= data.get('yonghu_area'),
        	yonghu_contact= data.get('yonghu_contact'),
        	yonghu_life= data.get('yonghu_life'),
            )
        yonghu1.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.yonghu2=alljishu.yonghu2+1
        alljishu.save()
        tongji =Tongji(tjid=yonghu1.yonghu_id,updatetime=datetime.now())
        tongji1=tongji.save()
        cz2=Caozuo(cztype ='公告',
            fy = '这个人什么都没写',
            fyshen='这个人什么都没写',
            fymi = 0, fystatus='正常有效',
            uid0 = yonghu1.yonghu_id,uid1 = yonghu1.yonghu_id,uname = yonghu1.yonghu_name,
            time0 = datetime.now(),time1 = datetime.now(),
        )
        cz2.save()
        cz3=Caozuo(cztype ='发言密码',
            fy = '初始密码八个1',
            fyshen='初始密码八个1',
            fymi = 0, fystatus='正常有效',
            id0=yonghu1.yonghu_id,id1=11111111,
            uid0 = yonghu1.yonghu_id,uid1 = yonghu1.yonghu_id,uname = yonghu1.yonghu_name,
            time0 = datetime.now(),time1 = datetime.now(),
        )
        cz3.save()
        
        # wd999=Wenduan.objects.all()
        # for item in wd999:
        #     item.wd_createtime=datetime.now()
        #     item.save()
        # for num in range(20000241,20001463):
        #     tongji =Tongji(tjid=num)
        #     tongji1=tongji.save()
        
        b={"okmsg":0}
    except:
        b={"okmsg":1}
    return JsonResponse(b, safe=False)

# 这是用于显示发言和附言的列表
@csrf_exempt
def show_fy_daishen(request):
    data = json.loads(request.body)
    fytype_ = data.get('type_')
    if fytype_=='fa':
        list1 =Caozuo.objects.filter(cztype='发言',fystatus='正在审核').order_by('-time1')
    if fytype_=='fu':
        list1 =Caozuo.objects.filter(~Q(cztype='发言')&~Q(cztype='修改')).order_by('-time1')
        list1 =list1.filter(fystatus='正在审核')
        
    list1=serializers.serialize("json",list1,fields=('cztype','fy','fytype','fyatt','fystatus','fyfanwei','fymi','id0','id1','title0','title1','type0','type1','uid1','uname','time0','time1','ding','cai','hui','fyhui','fujianshu','fyshen'))
    return JsonResponse(list1,safe=False)
    
# 审批通过，用户的附言和发言
@csrf_exempt
def shen_fy_pass(request):
    data = json.loads(request.body)
    kkk = data.get('kkk')
    kkk =int(kkk)
    list1 =Caozuo.objects.get(czid=kkk)
    list1.fystatus='正常有效'
    list1.time1=datetime.now()
    list1.fy=list1.fyshen
    list1.save()
    if list1.cztype=='发言':
        tongji1 = Tongji.objects.get(tjid=list1.uid0)
        tongji1.shenfayan=tongji1.shenfayan+1
        tongji1.save()
        alljishu = Alljishu.objects.get(keyid=999)
        alljishu.fayan=alljishu.fayan+1
        alljishu.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)
    
# 审批附言或发言，拒绝
@csrf_exempt
def shen_fy_reject(request):
    data = json.loads(request.body)
    kkk = data.get('kkk')
    kkk =int(kkk)
    list1 =Caozuo.objects.get(czid=kkk)
    list1.fystatus='已被拒绝'
    list1.save()
    if list1.cztype=='评论' and list1.id0>100000000:
        #这是如果评论的是一条附言，那就给附言的caozuo记录中的hui字段加一
        cz2=Caozuo.objects.get(czid=list1.id0)
        cz2.hui=cz2.hui-1
        cz2.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)
    
    
    #这就修改用户关注知识点的附言
@csrf_exempt
def edit_fyshen(request):
    data = json.loads(request.body)
    fuid  = data.get('fuid')
    fuyan  = data.get('fuyan')
    try:
        Caozuo.objects.filter(czid=fuid).update(fyshen=fuyan)
        b={"changed_ok":0}
        return JsonResponse(b, safe=False)
    except:
        b={"changed_ok":2}
        return JsonResponse(b, safe=False)
    return JsonResponse(b)

# 这是用户申请注册的列表
@csrf_exempt
def show_yh_daishen(request):
    data = json.loads(request.body)
    fystatus = data.get('status_')
    list1 =Yonghu.objects.filter(yonghu_status='正在审核').order_by('-yonghu_borntime')  
    list2 =Yonghu.objects.filter(yonghu_status='正常有效').order_by('-yonghu_fresh')    
    list1=serializers.serialize("json",list1)
    list2=serializers.serialize("json",list2)
    rr={'list1':list1,'list2':list2}
    return JsonResponse(rr,safe=False)
    
# 注册用户通过
@csrf_exempt
def shen_yh_pass(request):
    data = json.loads(request.body)
    kkk = data.get('kkk')
    kkk =int(kkk)
    list1 =Yonghu.objects.get(yonghu_id=kkk)
    list1.yonghu_status='正常有效'
    list1.save()
    alljishu = Alljishu.objects.get(keyid=999)
    alljishu.yonghu=alljishu.yonghu+1
    alljishu.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)

# 注册用户拒绝
@csrf_exempt
def shen_yh_reject(request):
    data = json.loads(request.body)
    kkk = data.get('kkk')
    kkk =int(kkk)
    list1 =Yonghu.objects.get(yonghu_id=kkk)
    list1.yonghu_status='已被拒绝'
    list1.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)
    
@csrf_exempt
def showxxjishu(request):
    data = json.loads(request.body)
    k  = int(data.get('k'))
    tongji1 = Tongji.objects.get(tjid=k)
    tongji1=tongji1.to_json()
    return JsonResponse(tongji1, safe=False)
    
@csrf_exempt
def changejishu(request):
    #前端借口有两个，一个是自动更新的数据矫正，一个是后台手动调整。
    #zhid，这是知识对象的id号。
    #jishu:这是更新后的数据
    #jitype:这是数据的类型，是zengfenxiang等还是其他类型
    data = json.loads(request.body)
    zhid  = int(data.get('zhid'))
    jishu  = int(data.get('jishu'))
    jitype  = data.get('jitype')
    try: 
        if zhid==999:
            alljishu=Alljishu.objects.get(keyid=999)
            if jitype=='yonghu':
                alljishu.yonghu=jishu
                alljishu.save()
            if jitype=='yonghu1':
                alljishu.yonghu1=jishu
                alljishu.save()              
            if jitype=='yonghu2':
                alljishu.yonghu2=jishu
                alljishu.save()            
            if jitype=='biaoqian':
                alljishu.biaoqian=jishu
                alljishu.save()
            if jitype=='qunzu':
                alljishu.qunzu=jishu
                alljishu.save()
            if jitype=='wenji':
                alljishu.wenji=jishu
                alljishu.save()
            if jitype=='fayan':
                alljishu.fayan=jishu
                alljishu.save()
            if jitype=='fuyan':
                alljishu.fuyan=jishu
                alljishu.save()
            if jitype=='wenduan':
                alljishu.wenduan=jishu
                alljishu.save()
        else:
            tongji1 = Tongji.objects.get(tjid=zhid)
            if jitype=='dianji':
                tongji1.dianji=jishu
                tongji1.save()
            if jitype=='guanzhu':
                tongji1.guanzhu=jishu
                tongji1.save()
            if jitype=='fenxiang':
                tongji1.fenxiang=jishu
                tongji1.save()
            if jitype=='biaoqian':
                tongji1.biaoqian=jishu
                tongji1.save()
            if jitype=='pinglun':
                tongji1.pinglun=jishu
                tongji1.save()
            if jitype=='guanlian':
                tongji1.guanlian=jishu
                tongji1.save()
            if jitype=='xiugai':
                tongji1.xiugai=jishu
                tongji1.save()
            if jitype=='neihan':
                tongji1.neihan=jishu
                tongji1.save()
            if jitype=='zengwenji':
                tongji1.zengwenji=jishu
                tongji1.save()
            if jitype=='zengbiaoqian':
                tongji1.zengbiaoqian=jishu
                tongji1.save()
            if jitype=='zengqunzu':
                tongji1.zengqunzu=jishu
                tongji1.save()
            if jitype=='zengfayan':
                tongji1.zengfayan=jishu
                tongji1.save()
            if jitype=='shenfayan':
                tongji1.shenfayan=jishu
                tongji1.save()
            if jitype=='zengfenxiang':
                tongji1.zengfenxiang=jishu
                tongji1.save()
        rr={'msg':0}
        return JsonResponse(rr,safe=False)
    except:
        rr={'msg':1}
        return JsonResponse(rr,safe=False)
        
    #这是在用户登录后，加载主页后，读取全站的宏观数据
@csrf_exempt
def show_users_denglu(request):
    data = json.loads(request.body)
    k  = data.get('k')
    countall = Tongji.objects.filter(tjid__gt=90000000,tjid__lt=100000000).order_by('-updatetime')
    countall=countall.to_json()
    return JsonResponse(countall, safe=False)

#这是例外处理的代码
@csrf_exempt
def deletemongoid(request):
    data = json.loads(request.body)
    kkk  = data.get('kkk')
    # tongji0=Tongji.objects.get(tjid=90000001)
    # tongji0.liaofreshtime=timezone.now()
    # tongji0.save()
    # liaodata0 =Liaodata(userid=90000000,createtime=datetime.now())
    # liaodata0=liaodata0.save()
    # liaodata0=liaodata0.to_json()
    liaolist0=Liaolist.objects.filter(userid0=90000001).delete()
    # count0 = Tongji.objects.filter(tjid__gt=200000000).delete()
    
    # return JsonResponse(tongji0.liaofreshtime, safe=False)
    return JsonResponse(liaolist0, safe=False)
    
    
#这是现实聊天列表的功能
@csrf_exempt
def sou_yh_info(request):
    data = json.loads(request.body)
    leixing  = int(data.get('leixing'))
    # userid  = int(data.get('yonghuid'))
    yonghu0=Yonghu.objects.get(yonghu_id=leixing)
    rr={'yhname':yonghu0.yonghu_name,'yhcontact':yonghu0.yonghu_contact}
    return JsonResponse(rr, safe=False)
    
#这是显示聊天计数等信息的模块
@csrf_exempt
def show_liao_data(request):
    data = json.loads(request.body)
    leixing  = int(data.get('leixing'))
    userid  = int(data.get('yonghuid'))
#以下是计算聊天室内有几条未读消息和多少分钟之前的刷新，
    liaodata=Liaodata.objects.filter(userid=userid,leixing=9)
    if liaodata:
        liaodata0=Liaodata.objects.get(userid=userid,leixing=9)
        liaodata9=Liaodata.objects.get(leixing=90000000,userid=0)
        jishu=liaodata9.zongshu-liaodata0.jishu
        jishi=liaodata0.freshtime
    else:
        jishu='?'
        jishi='?'
#以下是计算有几个用户对本用户进行的聊天
    liaodata0=Liaodata.objects.filter(userid=userid)
    if liaodata0:
        array0 = []
        for data0 in liaodata0:
            if data0.zongshu!=data0.jishu and data0.leixing!=9:
                yonghu_name9=id_transfer(data0.leixing)
                aaa = { 'yhid': data0.leixing,
                        'yhname': yonghu_name9,
                        'jishucha':data0.zongshu-data0.jishu,
                }
                array0.append(aaa)
        rr={'jishu':jishu,'jishi':jishi,'userlist':array0}
        return JsonResponse(rr, safe=False)
    else:
        rr={'jishu':jishu,'jishi':jishi,'userlist':[]}
        return JsonResponse(rr, safe=False)

    
#这是显示聊天内容列表的模块，
@csrf_exempt
def show_liao_list(request):
    data = json.loads(request.body)
    leixing  = int(data.get('leixing'))
    userid  = int(data.get('userid'))
    #以下判断，如果是90000000，则是显示聊天室的聊天记录
    if leixing==90000000:
        #以下判断，如果用户在聊天室的记录如果存在，就先读取记录，再更新记录
        liaodata=Liaodata.objects.filter(userid=userid,leixing=9)
        if liaodata:
            liaodata0=Liaodata.objects.get(userid=userid,leixing=9)
            liaodata9=Liaodata.objects.get(leixing=90000000,userid=0)
            jishu=liaodata9.zongshu-liaodata0.jishu
            jishi=liaodata9.createtime
            xinshi=liaodata0.freshtime
            
            liaodata0.jishu=liaodata9.zongshu
            # liaodata0.createtime=datetime.now()
            liaodata0.freshtime=timezone.now()
            liaodata0.save()
        else:
            #以下判断，如果用户在聊天室的记录不存在，则要创建一个记录
            jishu='?'
            jishi='?'
            xinshi=timezone.now()
            yonghu0=Yonghu.objects.get(yonghu_id=userid)
            liaodata1=Liaodata(
                userid=userid,
                username=yonghu0.yonghu_name,
                leixing=9,
                jishu=0,
                freshtime=timezone.now(),
                )
            liaodata1.save()
        liaolist9=Liaolist.objects.filter(leixing=90000000).order_by('-shentime')
        liaolist9=liaolist9.to_json()
        rr={'ll0':liaolist9,'jishu':jishu,'jishi':jishi,'xinshi':xinshi}
        return JsonResponse(rr, safe=False)
    else:
        liaolistx=Liaolist.objects(userid0=userid,leixing=leixing)
        liaolistx1=Liaolist.objects(userid0=leixing,leixing=userid)
        arrayx=[]
        for llx in liaolistx:
            llll={
                  'userid1':llx.userid1,
                  'username':llx.username,
                  'leixing':llx.leixing,
                  'huifuid':llx.huifuid,
                  'huifuname':llx.huifuname,
                  'zhid':llx.zhid,
                  'zhititle':llx.zhititle,
                  'zhitype':llx.zhitype,
                  'taidu':llx.taidu,
                  'fy':llx.fy,
                  'fystatus':llx.fystatus,
                  'fyshu':llx.fyshu,
                  'shentime':llx.shentime,
            }
            arrayx.append(llll)
        for llx in liaolistx1:
            llll={
                #   'id':llx._id,
                  'userid1':llx.userid1,
                  'username':llx.username,
                  'leixing':llx.leixing,
                  'huifuid':llx.huifuid,
                  'huifuname':llx.huifuname,
                  'zhid':llx.zhid,
                  'zhititle':llx.zhititle,
                  'zhitype':llx.zhitype,
                  'taidu':llx.taidu,
                  'fy':llx.fy,
                  'fystatus':llx.fystatus,
                  'fyshu':llx.fyshu,
                  'shentime':llx.shentime,
            }
            arrayx.append(llll)
        arrayx.sort(key = lambda x:x["shentime"], reverse=True)
        
        liaodataX=Liaodata.objects.filter(userid=userid,leixing=leixing)
        if liaodataX:
            liaodata_x=Liaodata.objects.get(userid=userid,leixing=leixing)
            jishu=liaodata_x.zongshu-liaodata_x.jishu
            jishi=liaodata_x.createtime
            xinshi=liaodata_x.freshtime
            liaodata_x.jishu=liaodata_x.zongshu
            # liaodata_x.freshtime=timezone.now()
            liaodata_x.save()
            rr={'ll0':arrayx,'jishu':jishu,'jishi':jishi,'xinshi':xinshi}
            return JsonResponse(rr, safe=False)
        else:
            jishu='?'
            jishi='?'
            xinshi=timezone.now()
            yonghuX=Yonghu.objects.get(yonghu_id=userid)
            liaodataX=Liaodata(
                userid=userid,
                username=yonghuX.yonghu_name,
                leixing=leixing,
                zongshu=0,
                jishu=0,
                # createtime=timezone.now(),
                # freshtime=timezone.now(),
                )
            liaodataX.save()
            rr={'ll0':arrayx,'jishu':jishu,'jishi':jishi,'xinshi':xinshi}
            return JsonResponse(rr, safe=False)
        
        
#这是现实聊天列表的功能
@csrf_exempt
def add_liaomsg(request):
    data = json.loads(request.body)
    yonghuid=int(data.get('yonghuid'))
    yonghuname=data.get('yonghuname')
    mi=data.get('mi')
    taidu=data.get('taidu')
    niming=data.get('niming')
    zhid=int(data.get('zhid'))
    hf_yhid=int(data.get('hf_yhid'))
    hf_yhname=data.get('hf_yhname')
    hf_content=data.get('hf_content')
    leixing=int(data.get('leixing'))
    fymm=data.get('fymm')
    if mi==1:#加密的明文信息，现将发言内容暂时存在fyshen中，待审批通过之后，在转入fy中。
        fystatus='正常有效'
        fyshu=len(hf_content)
        DES_SECRET_KEY = fymm
        des_obj = des(DES_SECRET_KEY, ECB, DES_SECRET_KEY, padmode=PAD_PKCS5)  # 初始化一个des对象
        hf_content = hf_content.encode('gb2312')# # 这里中文要转成字节， 英文好像不用
        hf_content = des_obj.encrypt(hf_content)   # 用对象的encrypt方法加密
        fy = base64.b64encode(hf_content)
        fyshen=''
    else:
        fystatus='正在审核'
        fyshu=0
        fyshen=hf_content
        fy='正在审核'
    # # try:
    # if hf_yhid>90000000:
    #     yonghu0=Yonghu.objects.get(yonghu_id=hf_yhid)
    #     huifuname=yonghu0.yonghu_name
    # else:
    #     huifuname=''
    
    if zhid>10000000:
        zhitype,zhititle=id_transfer(zhid)
    else:
        zhitype=''
        zhititle=''
        
    if niming==True:
        yonghuname='匿名'
        yonghuid=99999999
        
    liaolist0=Liaolist(
        userid0= yonghuid,
        userid1= yonghuid,
        username=yonghuname,
        leixing=leixing,
        fystatus=fystatus,
        
        huifuid=hf_yhid,
        huifuname=hf_yhname,
        
        zhid=zhid,
        zhititle=zhititle,
        zhitype=zhitype,
        
        taidu=taidu,
        fy=fy,
        fyshen=fyshen,
        fyshu=fyshu,
        createtime = datetime.now(),
        shentime = datetime.now(),
        )
    liaolist0.save()

    if leixing==90000000:
        #以下是用户在聊天室内聊天，变更聊天记录，leixing等于90000000且userid等于0是全量记录
        liaodata0 = Liaodata.objects.get(userid=0,leixing=90000000)
        liaodata0.zongshu=liaodata0.zongshu+1
        liaodata0.createtime=datetime.now()
        liaodata0.save()
         #以下userid=yonghuid,leixing=90000000是代表用户在聊天室内聊天的单独记录,为jishu+1
        liaodata00 = Liaodata.objects.filter(userid=yonghuid,leixing=9)
        if liaodata00:
            # liaodata00[0].jishu=liaodata00[0].jishu+1
            # liaodata00[0].createtime=datetime.now()
            # liaodata00[0].save()
            rr={'msg':0}
            return JsonResponse(rr,safe=False)
        else:
            # yonghu1=Yonghu.objects.get(yonghu_id=yonghuid)
            liaodata1=Liaodata(
                userid=yonghuid,
                # username=yonghu1.yonghu_name,
                leixing=9,
                jishu=1,
                zongshu=1,
                # createtime=datetime.now(),
                # freshtime=datetime.now(),
                )
            liaodata1.save()
        rr={'msg':0}
        return JsonResponse(rr,safe=False)
    else:
        liaodataX = Liaodata.objects.filter(userid=leixing,leixing=yonghuid)
        if liaodataX:
            liaodata_x=Liaodata.objects.get(userid=leixing,leixing=yonghuid)
            liaodata_x.zongshu=liaodata_x.zongshu+1
            # liaodata_x.createtime=datetime.now()
            liaodata_x.save()
        else:
            yonghuX=Yonghu.objects.get(yonghu_id=yonghuid)
            liaodataX1=Liaodata(
                userid=leixing,
                username=yonghuX.yonghu_name,#我方的名称
                leixing=yonghuid,
                zongshu=1,
                jishu=0,
                # createtime=datetime.now()
                )
            liaodataX1.save()
        liaodata_ = Liaodata.objects.filter(userid=yonghuid,leixing=leixing)
        if liaodata_:
            liaodata_x=Liaodata.objects.get(userid=yonghuid,leixing=leixing)
            liaodata_x.zongshu=liaodata_x.zongshu+1
            # liaodata_x.jishu=liaodata_x.jishu+1
            # liaodata_x.createtime=datetime.now()
            # liaodata_x.freshtime=datetime.now()
            liaodata_x.save()
        else:
            yonghuX=Yonghu.objects.get(yonghu_id=leixing)
            liaodata_=Liaodata(
                userid=yonghuid,
                username=yonghuX.yonghu_name,#对方的名称
                leixing=leixing,
                zongshu=1,
                jishu=0,
                # createtime=datetime.now(),
                # freshtime=datetime.now()
                )
            liaodata_.save()
        rr={'msg':0}
        return JsonResponse(rr,safe=False)
        
        

@csrf_exempt
def zhankai_liaoshen(request):
    data = json.loads(request.body)
    kkk=data.get('kkk')
    liaolist0=Liaolist.objects.filter(fystatus='正在审核').order_by('-shentime')
    liaolist0=liaolist0.to_json()
    return JsonResponse(liaolist0,safe=False)
    
    

@csrf_exempt
def shenliao_pass(request):
    data = json.loads(request.body)
    kkk=data.get('kkk')
    liaolist0=Liaolist.objects.get(id=kkk)
    liaolist0.fystatus='正常有效'
    liaolist0.fy=liaolist0.fyshen
    liaolist0.shentime=datetime.now()
    liaolist0.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)
    
@csrf_exempt
def shanliao(request):
    data = json.loads(request.body)
    kkk=data.get('kkk')
    liaolist0=Liaolist.objects.get(id=kkk)
    liaolist0.fystatus='删除失效'
    liaolist0.fy='已经删除'
    liaolist0.save()
    rr={'msg':0}
    return JsonResponse(rr,safe=False)
    
    
    
    
    
# 参考代码：
#     使用 MongoEngine 0.8或者更高版本，对象和querysets具有to_json()方法。
#     cs=Ceshi.objects.to_json()
#       max = a if a>b else b
    # name = request.POST.get('name', None)

# lt=client.fangjia.district_stat_all_0416
# dl = dt.find(query)

# bf=[]
# for m in dl:
#     bf.append(m)
#     if len(bf)==20000:
#         lt.insert_many(bf)
#         bf=[]
# lt.insert_many(bf)



# #作废不用
# @csrf_exempt
# def count3x(request):
#     data = json.loads(request.body)
#     userid = data.get('userid')
#     # chuan = data.get('chuan')
#     zoneid = data.get('zoneid')
#     # if zoneid=='31':
#     #     c3x=Yonghu.objects.filter(yonghu_type='普通用户',yonghu_status='正常有效').count()
#     # if zoneid=='36':
#     #     c3x=Yonghu.objects.filter(yonghu_type='人物名片').count()
#     # if zoneid=='37':
#     #     c3x=Yonghu.objects.filter(yonghu_type='工团组织').count()
#     # if zoneid=='32':
#     #     uidlist=chuan_chaifen(chuan,'yh')
#     #     c3x=len(uidlist)
#     # if zoneid=='33':
#     userid = int(userid)
#     list1 =Caozuo.objects.filter(cztype="关注",id0=userid)
#     list1=list1.filter(Q(fystatus="正常有效")|Q(fystatus="正在审核")).values('uid0')
#     array1 = []
#     for l1 in list1:
#         arr1 = l1['uid0']
#         array1.append(arr1)
#     c3x=Yonghu.objects.filter(yonghu_id__in = array1).count()
#     # if zoneid=='34':
#     #     c3x=Qunzu.objects.filter(qz_status='正常有效').count()
#     # if zoneid=='35':
#     #     qzlist=chuan_chaifen(chuan,'qz')
#     #     c3x=len(qzlist)
#     return JsonResponse(c3x, safe=False)


# #作废不用
# #这是为了计数用户关注的知识点等，用来接收前端的知识点id串，然后拆分为各种计数，作废不用
# @csrf_exempt
# def count2x(request):
#     data = json.loads(request.body)
#     chuan = data.get('chuan')
#     cz1=chuan.split('_'); 
#     cz2=[]
#     wj=0
#     wd=0
#     bq=0
#     qz=0
#     yh=0
#     fy=0
#     for k in cz1:
#         if k =='':
#             pass
#         else:
#             k=int(k)
#             if k>90000000 and k<99999999:
#                 yh=yh+1
#             if k>80000000 and k<90000000:
#                 qz=qz+1
#             if k>30000000 and k<40000000:
#                 bq=bq+1
#             if k>10000000 and k<20000000:
#                 wj=wj+1
#             if k>20000000 and k<30000000:
#                 wd=wd+1
#             if k>100000000:
#                 fy=fy+1
#     list1={
#         "wj":wj,
#         "wd":wd,
#         "bq":bq,
#         "qz":qz,
#         "yh":yh,
#         "fy":fy,
#     }
#     return JsonResponse(list1,safe=False)

