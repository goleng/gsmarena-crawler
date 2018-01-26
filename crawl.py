from pyquery import PyQuery as pq
from lxml import etree
from time import time
import urllib.request
import asyncio
import aiohttp
import json

URL = 'https://www.gsmarena.com/'

started_at = time()

makers = []
models = []
specs = []

def get_time():
  return '[{:.2f} sec]'.format(time() - started_at)

def get_makers():
  d = pq(URL + 'makers.php3')
  for maker in d('.main-makers td a'):
    makers.append({
      'brand': maker.text,
      'url': maker.get('href'),
      'model_count': int(maker.findtext('span').split(' ')[0]),
    })

async def get_models(maker):
  try:
    url = URL + maker['url']
    while True:
      async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
          d = pq(await res.text())
      for model in d('.makers a'):
        spec = {
          'brand': maker['brand'],
          'url': model.get('href'),
        }
        models.append(spec)
      if len(models) == maker['model_count']:
        break
      else:
        try:
          url = URL + d('.pages-next')[0].get('href')
          if d('.pages-next')[0].get('href')[0] == '#':
            break
        except:
          break
  except:
    print(get_time(), 'error', url)

async def get_all_models(makers):
  tasks = [asyncio.ensure_future(get_models(maker)) for maker in makers]
  await asyncio.wait(tasks)

async def get_specs(model):
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(URL + model['url']) as res:
        d = pq(await res.text())
    for item in d('*[data-spec]'):
      if item.get('data-spec'):
        model[item.get('data-spec')] = (item.text or '') + ''.join([etree.tostring(child).decode('utf-8') for child in item.iterchildren()])
    model['hits'] = d('.help-popularity span')[0].text
    model['hits_percent'] = d('.help-popularity strong')[0].getchildren()[0].tail
    model['fans'] = d('.specs-fans strong')[0].getchildren()[0].tail
    specs.append(model)
  except:
    print(get_time(), 'error', URL + model['url'])

INTERVAL = 200
async def get_all_specs(models):
  for i in range(0, len(models), INTERVAL):
    tasks = [asyncio.ensure_future(get_specs(model)) for model in models[i:i + INTERVAL]]
    await asyncio.wait(tasks)
    print(get_time(), len(specs), '/', len(models), 'specs')

if __name__ == '__main__':
  print(get_time(), 'collecting makers...')
  get_makers()
  model_count = sum(maker['model_count'] for maker in makers)
  print(get_time(), len(makers), 'makers,', model_count, 'models')
  print(get_time(), 'collecting models...')
  ioloop = asyncio.get_event_loop()
  ioloop.run_until_complete(get_all_models(makers))
  print(get_time(), len(models), 'models actually collected.')
  print(get_time(), 'collecting specs...')
  ioloop.run_until_complete(get_all_specs(models))
  print(get_time(), len(specs), 'specs actually collected.')
  ioloop.close()
  print(get_time(), 'writing json')
  with open('data.json', 'w') as f:
    json.dump(specs, f)
  print(get_time(), 'done')
