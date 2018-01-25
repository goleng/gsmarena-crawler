from pyquery import PyQuery as pq
from lxml import etree
from time import time
import json

URL = 'https://www.gsmarena.com/'

started_at = time()

def get_makers():
  makers = []
  d = pq(URL + 'makers.php3')
  for maker in d('.main-makers td a'):
    makers.append({
      'brand': maker.text,
      'url': maker.get('href'),
      'model_count': int(maker.findtext('span').split(' ')[0]),
    })
  return makers

def get_models(maker):
  models = []
  d = pq(URL + maker['url'])
  while True:
    for model in d('.makers a'):
      spec = {
        'brand': maker['brand'],
        'url': model.get('href'),
      }
      e = pq(URL + spec['url'])
      for item in e('*[data-spec]'):
        if item.get('data-spec'):
          spec[item.get('data-spec')] = (item.text or '') + ''.join([etree.tostring(child).decode('utf-8') for child in item.iterchildren()])
      spec['hits'] = e('.help-popularity span')[0].text
      spec['hits_percent'] = e('.help-popularity strong')[0].getchildren()[0].tail
      spec['fans'] = e('.specs-fans strong')[0].getchildren()[0].tail
      models.append(spec)
      print(maker['brand'], len(models), '/', maker['model_count'], int(time() - started_at))
    if len(models) == maker['model_count']:
      break
    else:
      d = pq(URL + d('.pages-next')[0].get('href'))
  return models

if __name__ == '__main__':
  makers = get_makers()
  model_count = sum(maker['model_count'] for maker in makers)
  print(len(makers), 'makers /', model_count, 'models')
  models = []
  for maker in makers:
    models += get_models(maker)
    print(len(models), '/', model_count, 'models', int(time() - started_at))
  with open('data.json', 'w') as f:
    json.dump(models, f)
  print(int(time() - started_at))
