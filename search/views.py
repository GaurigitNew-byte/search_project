import os
import csv
import requests
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.views import View
from .client import RestClient
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

#Load eviroments variables from .env file
load_dotenv()
DATA_FOR_SEO_USERNAME = os.getenv('USERNAME')
DATA_FOR_SEO_PASSWORD = os.getenv('PASSWORD')

class SearchViewPage(View):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        #Retrieve saved search results from session
        context = {
            "results": request.session.get("results", []),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Get the queries from the post request and remove extra spaces and empty queries
        queries = self.request.POST.getlist("q")
        queries = [q.strip() for q in queries if q.strip()]

        results = []

        if not queries:
            #If no queries provides show error message with saved search result from the session
            results = self.request.session.get("results", [])
            messages.error(request, "Please enter alteast one search query.")
            return render(self.request, self.template_name, {"results": results})

        #Creating Api cleint for DataForSEO
        try:
            client = RestClient(DATA_FOR_SEO_USERNAME, DATA_FOR_SEO_PASSWORD)
        except Exception as e:
            messages.error(request, f"Failed to initialize DataForSEO client: {e}")
            return render(self.request, self.template_name, {"results": results})
        
        with ThreadPoolExecutor(max_workers=min(10, len(queries))) as executor:
            future_results = {executor.submit(self.fetch_query_results,client,q): q for q in queries}
            for future in as_completed(future_results):
                query = future_results[future]
                try:
                    response = future.result()
                    results.extend(response)
                except Exception as e:
                    messages.error(request, f"Error fetching results for '{query}': {e}")
        if results:
            messages.success(request, "Search completed successfully!")
        else:
            messages.warning(request, "No results found.")
        
        #Save result to the session
        request.session["results"] = results
        return render(request, self.template_name, {"results": results})
    
    def fetch_query_results(self,client,query):
        results = []
        post_data = {}
        post_data[0] = {
            "language_code": "en",
            "location_code": 2840,
            "keyword": query
        }
        try:
            response = client.post("/v3/serp/google/organic/live/regular", post_data)
            #For debugging
            print(response)

            if response.get("status_code") == 20000:
                #Parse the response and extract the result items
                tasks = response.get("tasks", [])
                for task in tasks:
                    for res in task.get('result',[]):
                        for item in res.get('items',[]):
                            results.append({
                            "query": query,
                            "title": item.get("title", ""),
                            "link": item.get("url", ""),
                            "snippet": item.get("description", ""),
                        })            
            else:
                raise Exception(f"Error: {response["status_code"], response["status_message"]}")
        except requests.exceptions.ConnectionError:
            raise Exception("Network error: Unable to connect to DataForSEO API.")
        except requests.exceptions.Timeout:
            raise Exception("Network error: Request to DataForSEO API timed out.")
        except Exception as e:
            raise Exception(f"Failed to fetch results for query '{query}': {e}")
        return results


class DownloadCSVView(View):
    template_name = 'home.html'
    def get(self,request,*args, **kwargs):
        #Fetch saved results from the session
        results = self.request.session.get('results',[])
        if not results:
            messages.error(self.request, "No results to download.")
            return render(request, self.template_name)
        response = HttpResponse(content_type='text/csv')
        response['content'] = 'attachment; filename="search_results.csv"'
        #Generating CSV file
        writer = csv.writer(response)
        writer.writerow(['Query', 'Title', 'Link', 'Snippet'])
        for result in results:
            writer.writerow([result['query'], result['title'], result['link'], result['snippet']])
        return response