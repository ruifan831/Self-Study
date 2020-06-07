from django.shortcuts import render
from SPARQLWrapper import SPARQLWrapper, JSON
from django.http import HttpResponse,JsonResponse
import json
import time
from collections import defaultdict
import random
import itertools

# Create your views here.
sparql = SPARQLWrapper("http://localhost:3030/db/query")

# Add the two views we have been talking about  all this time :)
 
def index(request):
    return render(request, 'queryPage/index.html')

def query(request):
    return render(request,'queryPage/query.html')
     
def data(request):
    queryString="""
        PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX os: <http://www.w3.org/2000/10/swap/os#>
        PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select ?main_label ?sub_label ?kp_label where{
        ?main rdf:type osf:MainCategory;
                osf:has_subcategory ?sub;
                rdfs:label ?main_label.
        ?sub rdf:type osf:SubCategory;
            rdfs:label ?sub_label;
            osf:has_knowledge_point ?kp.
        ?kp rdfs:label ?kp_label.
        
        } 
    """
    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    main_dict = defaultdict(set)
    sub_dict = defaultdict(set)

    for i in results["results"]["bindings"]:
        main_dict[i['main_label']['value']].add(i['sub_label']['value'])
        sub_dict[i['sub_label']['value']].add(i['kp_label']['value'])
    data_pie=[]
    result=[]
    merged = list(set(list(itertools.chain(*list(sub_dict.values())))))
    kp_dict=dict(zip(merged,range(1,len(merged)+1)))
    sub_merged = list(set(list(itertools.chain(*list(main_dict.values())))))
    sub_to_val_dict = dict(zip(sub_merged,range(1,len(sub_merged)+1)))
    for k,v in main_dict.items():
        data_pie.append({"value":len(v), "name":k})
        
        temp_dict = {}
        temp_dict["name"] = k
        temp_dict['children']= []
        for i in v:
            temp_children_dict = {}
            temp_children_dict["name"] = i
            temp_children_dict["value"] = len(sub_dict[i])
            # temp_children_dict["children"]=[{"name":j,'value':1} for j in sub_dict[i]]
            temp_dict["children"].append(temp_children_dict)
        result.append(temp_dict)
    queryString = """
        PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX os: <http://www.w3.org/2000/10/swap/os#>
        PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select ?kp_label (count(?course) as ?course_count) where{
        ?kp rdfs:label ?kp_label;
            rdf:type osf:KnowledgePoint.
        ?course osf:teach ?kp;
        } group by ?kp_label
        order by desc(?course_count)
        limit 100
    """
    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    kp_course_count=[]
    for i in results["results"]["bindings"]:
        temp_dict={
            "name":i["kp_label"]['value'],
            "value":int(i['course_count']['value'])
        }
        kp_course_count.append(temp_dict)
    return JsonResponse({"data":{"name":"root","children":result},"kp_count":kp_course_count})

def detailAPI(request):
    if request.method == "GET":
        course = request.GET.get("course",None)
        mainCate = request.GET.get("mainCategory",None)
        subCate = request.GET.get("subcategory",None)
        kp = request.GET.get("kp",None)
        print(kp)
        kp_re = request.GET.get("kp_re",None)
        if kp_re:
            kp = kp_re
        page=int(request.GET.get('p',0))*10
        if course:
            # get course basic information except instructor and Category
            queryString = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX os: <http://www.w3.org/2000/10/swap/os#>
                PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
                select distinct ?course_title ?course_url ?num_sub ?rating ?img_url ?des ?insturction_level ?kp_label where{
                osf:%s rdf:type osf:Course;
                    rdfs:label ?course_title;
                    osf:teach ?kp;
                    osf:course_rating ?rating;
                    osf:course_num_subscribers ?num_sub;
                    osf:course_url ?course_url;
                    osf:instruction_level ?insturction_level;
                    osf:course_img ?img_url;
                    osf:course_description ?des.
                    ?kp rdfs:label ?kp_label.
                }
            """%(course)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            course_dict=defaultdict(set)
            for i in results["results"]["bindings"]:
                course_dict['course'].add(i['course_title']['value'])
                course_dict['course_url'].add(i['course_url']['value'])
                course_dict["num_sub"].add(i["num_sub"]["value"])
                course_dict["rating"].add(i["rating"]["value"])
                course_dict["img_url"].add(i["img_url"]["value"])
                course_dict['des'].add(i["des"]['value'])
                course_dict["instruction_level"].add(i["insturction_level"]["value"][i["insturction_level"]["value"].find("#")+1:])
                course_dict["kp"].add(i["kp_label"]["value"])
            queryString="""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX os: <http://www.w3.org/2000/10/swap/os#>
                PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
                select distinct ?sub_label ?main_label where{
                osf:%s rdf:type osf:Course;
                    osf:teach ?kp.
                ?sub osf:has_knowledge_point ?kp;
                    rdfs:label ?sub_label.
                ?main osf:has_subcategory ?sub;
                        rdfs:label ?main_label.
                }          
            """%(course)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for i in results["results"]["bindings"]:
                course_dict['subcate'].add(i['sub_label']['value'])
                course_dict['main'].add(i['main_label']['value'])

            queryString="""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX os: <http://www.w3.org/2000/10/swap/os#>
                PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
                select distinct ?kp_re_label where{
                osf:%s rdf:type osf:Course;
                    osf:teach ?kp.
                ?kp_re osf:is_prerequisite ?kp;
                        rdfs:label ?kp_re_label.
                }
            """%(course)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            if results["results"]["bindings"]:
                for i in results["results"]["bindings"]:
                    course_dict['kp_re'].add(i['kp_re_label']['value'])
            else:
                course_dict['kp_re']=set()
            
            queryString="""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX os: <http://www.w3.org/2000/10/swap/os#>
                PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
                select distinct ?instructor_name ?instructor_url where{
                osf:%s rdf:type osf:Course;
                            osf:has_instructor ?instructor.
                ?instructor rdfs:label ?instructor_name;
                            osf:instructor_url ?instructor_url
                }
            """%(course)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            if results["results"]["bindings"]:
                for i in results["results"]["bindings"]:
                    course_dict['instructor'].add(i['instructor_name']['value'])
                    course_dict['instructor_url'].add(i['instructor_url']['value'])
            else:
                course_dict['instructor'].add("Unspecified")
                course_dict['instructor_url'].add("#")
            final_return={}
            for k,v in course_dict.items():
                final_return[k]=list(v)
            print(final_return["img_url"])
            return JsonResponse(final_return)
        elif mainCate:
            querystring="""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX os: <http://www.w3.org/2000/10/swap/os#>
            PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
            select distinct ?course ?course_title ?sub_label where{
            ?course osf:teach ?kp;
                    rdfs:label ?course_title.
            ?subcate osf:has_knowledge_point ?kp;
                    rdfs:label ?sub_label.
            ?mainCate osf:has_subcategory ?subcate;
                        rdfs:label "%s".
            }
            limit 10
            offset %d
            """%(mainCate,page)
            sparql.setQuery(querystring)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            final_list=[]
            for i in results["results"]["bindings"]:
                final_list.append((i['course']['value'][i['course']['value'].find("#")+1:],i["course_title"]['value'],i['sub_label']['value']))

            return JsonResponse(final_list,safe=False)
        elif subCate:
            queryString="""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX os: <http://www.w3.org/2000/10/swap/os#>
            PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
            select distinct ?kp_label where{
                ?subcate osf:has_knowledge_point ?kp;
                rdfs:label "%s".
            ?kp rdfs:label ?kp_label.
            }
            limit 10
            offset %d
            """%(subCate,page)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            final_list=[]
            for i in results["results"]["bindings"]:
                final_list.append(i["kp_label"]['value'])
            return JsonResponse(final_list,safe=False)
        elif kp or kp_re:
            queryString="""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX os: <http://www.w3.org/2000/10/swap/os#>
            PREFIX ods: <http://lod.xdams.org/ontologies/ods/>
            select distinct ?course ?course_title ?sub_label where{
                ?subcate osf:has_knowledge_point ?kp;
                rdfs:label ?sub_label.
            ?kp rdfs:label "%s";
                rdf:type osf:KnowledgePoint.
            ?course osf:teach ?kp;
                    rdfs:label ?course_title.
                        }
            limit 10
            offset %d
            """%(kp,page)
            sparql.setQuery(queryString)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            final_list=[]
            for i in results["results"]["bindings"]:
                course_id = i["course"]["value"][i["course"]["value"].find("#")+1:]
                final_list.append((course_id,i["course_title"]["value"],i["sub_label"]['value']))
            return JsonResponse(final_list,safe=False)


def detail(request):
    course = request.GET.get("course",None)
    mainCate = request.GET.get("mainCategory",None)
    subCate = request.GET.get("subcategory",None)
    kp = request.GET.get("kp",None)
    kp_re = request.GET.get("kp_re",None)
    if kp_re:
        kp= kp_re
    if course:
        return render(request,"queryPage/detailCourse.html",{"title":course})
    elif mainCate:
        return render(request,"queryPage/detailMain.html",{"title":mainCate})
    elif subCate:
        return render(request,"queryPage/detailSub.html",{"title":subCate})
    elif kp:
        return render(request,"queryPage/detailKp.html",{"title":kp})


def searchApi(request):
    if request.method == "GET":
        keyword = request.GET.get("searchInput").replace("+"," ")
        searchField =request.GET.get("searchField").replace("+"," ")
        print(keyword)
        print(searchField)
        page=int(request.GET.get('p',0))*10
        queryString="""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX osf: <http://www.semanticweb.org/ruifanxu/ontologies/2020/3/inf558_project#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select distinct ?course ?course_title ?img_url where{
        ?course rdf:type osf:Course;
                rdfs:label ?course_title;
                osf:course_url ?course_url;
                osf:teach ?kp;
                osf:course_img ?img_url.
        ?kp rdf:type osf:KnowledgePoint;
            rdfs:label ?kp_label.
        ?subcate rdf:type osf:SubCategory;
                osf:has_knowledge_point ?kp;
                rdfs:label ?sub_label.
        ?mainCate rdf:type osf:MainCategory;
                    osf:has_subcategory ?subcate;
                    rdfs:label ?main_label.
        filter(regex(%s,"%s","i"))
        }
        limit 10
        offset %d
        """

        queryDict={
            'Course':queryString%("?course_title",keyword,page),
            'Main Category':queryString%("?main_label",keyword,page),
            'SubCategory':queryString%("?sub_label",keyword,page),
            'Knowledge Point':queryString%("?kp_label",keyword,page),
            'Required Knowledge Point':queryString%("?kp_label",keyword,page),
        }

        sparql.setQuery(queryDict.get(searchField))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        results= list(map(lambda x:(x["course"]["value"],x['course_title']['value'],x['img_url']['value']),results["results"]["bindings"]))
        return JsonResponse(results,safe=False)
    

def search(request):
    keyword = request.GET.get("searchInput")
    table_column=["Course Title","Main Category","Subcategory","Knowledge Point"]
    return render(request,'queryPage/search.html',{'keyword':keyword,'columns':table_column})
