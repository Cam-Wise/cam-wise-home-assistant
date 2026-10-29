from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
import pytest
from aiohttp import web
from homeassistant.helpers import entity_registry as er
from custom_components.cam_wise import recordings as rec, recording_providers as pro

async def test_ring_opaque_and_bound(hass):
 row=er.async_get(hass).async_get_or_create('camera','ring','synthetic')
 entry=NS(entry_id='cw')
 hass.states.async_set(row.entity_id,'idle',{'last_video_id':123,'video_url':'https://secret.test'})
 result=await rec.async_list_recordings(hass,entry,row.entity_id)
 assert len(result['recordings'])==1 and 'secret.test' not in str(result)
 with pytest.raises(web.HTTPNotFound):
  await rec.async_download_recording(hass,None,NS(entry_id='other'),row.entity_id,result['recordings'][0]['id'])

async def test_unifi_filter(hass,monkeypatch):
 rows=[{'id':'valid','camera':'selected','start':1,'end':2},{'id':'wrong','camera':'other','start':1,'end':2},{'id':'ongoing','camera':'selected','start':1,'end':None}]
 cam=NS(device=NS(id='selected'),data=NS(api=NS(is_public_only=False,get_events_raw=AsyncMock(return_value=rows))))
 monkeypatch.setattr(pro,'entity',lambda *a:cam)
 assert await pro.list_sources(hass,NS(platform='unifiprotect'),'camera.selected')==[('valid','1','1:2',{'captured_at':.001,'ended_at':.002,'completed':True})]
 cam.data.api.is_public_only=True
 with pytest.raises(web.HTTPConflict):await pro.list_sources(hass,NS(platform='unifiprotect'),'camera.selected')

async def test_blink_origin(hass,monkeypatch):
 api=NS(recent_clips=[{'clip':'https://evil.test/a.mp4','time':'today'},{'clip':'https://vendor.test/old.mp4','time':'old'}],clip='https://vendor.test/new.mp4',last_record='today',sync=NS(urls=NS(base_url='https://vendor.test')))
 monkeypatch.setattr(pro,'entity',lambda *a:NS(_camera=api))
 rows=await pro.list_sources(hass,NS(platform='blink'),'camera.selected')
 assert len(rows)==2 and all('evil' not in row[0] for row in rows)

async def test_tapo_fail_closed(hass,monkeypatch):
 monkeypatch.setattr(pro,'entity',lambda *a:object())
 hass.data['tapo_control']={'entry':{'entities':[],'childDevices':[]}}
 with pytest.raises(web.HTTPConflict):pro.tapo_device(hass,NS(config_entry_id='entry'),'camera.selected')

async def test_provider_dispatch(hass,monkeypatch):
 for provider in ('unifiprotect','tapo_control','blink'):
  row=er.async_get(hass).async_get_or_create('camera',provider,'synthetic-'+provider)
  monkeypatch.setattr(pro,'list_sources',AsyncMock(return_value=[('["20261028",100,200]' if provider=='tapo_control' else 'private-source','clip')]))
  result=await rec.async_list_recordings(hass,NS(entry_id='cw'),row.entity_id)
  assert result['provider']==provider and 'private-source' not in str(result)

async def test_unsupported(hass):
 row=er.async_get(hass).async_get_or_create('camera','generic','synthetic')
 with pytest.raises(web.HTTPBadRequest):await rec.async_list_recordings(hass,NS(entry_id='cw'),row.entity_id)

async def test_tapo_completed_only(hass,monkeypatch):
 import sys,types
 utils=types.ModuleType('custom_components.tapo_control.utils')
 utils.getRecordings=AsyncMock(return_value=[{'clip':{'startTime':100,'endTime':200}},{'ongoing':{'startTime':300,'endTime':10**12}}])
 monkeypatch.setitem(sys.modules,'custom_components.tapo_control.utils',utils)
 cam=object()
 device={'entities':[{'entity':cam}],'controller':NS(getRecordingsList=lambda:[{'day':{'date':'20261028'}}]),'timezoneOffset':0}
 hass.data['tapo_control']={'entry':device}
 monkeypatch.setattr(pro,'entity',lambda *a:cam)
 rows=await pro.list_sources(hass,NS(platform='tapo_control',config_entry_id='entry'),'camera.selected')
 assert len(rows)==1 and '100' in rows[0][0]

async def test_blink_download_bound(hass,monkeypatch):
 response=NS(release=lambda:None)
 cam=NS(_camera=NS(get_video_clip=AsyncMock(return_value=response)))
 monkeypatch.setattr(pro,'entity',lambda *a:cam)
 monkeypatch.setattr(pro,'list_sources',AsyncMock(return_value=[('https://vendor.test/clip','clip')]))
 monkeypatch.setattr(pro,'stream_upstream',AsyncMock(return_value='stream'))
 assert await pro.download_source(hass,None,NS(platform='blink'),'camera.selected','https://vendor.test/clip')=='stream'
 cam._camera.get_video_clip.assert_awaited_once_with(url='https://vendor.test/clip')
 with pytest.raises(web.HTTPNotFound):await pro.download_source(hass,None,NS(platform='blink'),'camera.selected','https://vendor.test/other')

async def test_reolink_channel_binding(hass,monkeypatch):
 from pytest_homeassistant_custom_component.common import MockConfigEntry
 vendor=MockConfigEntry(domain='reolink',data={});vendor.add_to_hass(hass)
 row=er.async_get(hass).async_get_or_create('camera','reolink','serial_0_sub',config_entry=vendor)
 eid=row.config_entry_id
 cam=NS(identifier=f'CAM|{eid}|0',thumbnail='/api/camera_proxy/'+row.entity_id,media_content_id='cam')
 resolution=NS(identifier=f'RES|{eid}|0|sub',media_content_id='res')
 day=NS(identifier=f'DAY|{eid}|0|sub|2026|10|28',media_content_id='day')
 clip=NS(identifier=f'FILE|{eid}|0|sub|filename|100|200',media_content_id=f'media-source://reolink/FILE|{eid}|0|sub|filename|100|200',can_play=True,title='clip')
 wrong=NS(identifier='FILE|other|1|sub|secret|100|200',media_content_id='media-source://reolink/other',can_play=True,title='wrong')
 async def browse(hass,identifier):return NS(children={'media-source://reolink':[cam],'cam':[resolution],'res':[day],'day':[clip,wrong]}[identifier])
 monkeypatch.setattr(rec.media_source,'async_browse_media',browse)
 result=await rec.async_list_recordings(hass,NS(entry_id='cw'),row.entity_id)
 assert len(result['recordings'])==1 and 'wrong' not in str(result)


async def test_recording_bridge_authorization(hass,hass_client,entry,api,monkeypatch):
 from homeassistant.setup import async_setup_component
 from custom_components.cam_wise.client import CamWiseApiError
 await async_setup_component(hass,'http',{})
 hass.config_entries.async_update_entry(entry,data={**entry.data,'pairing_token':'synthetic-recordings'})
 assert await hass.config_entries.async_setup(entry.entry_id)
 await hass.async_block_till_done()
 reader=AsyncMock(return_value={'provider':'ring','recordings':[]})
 monkeypatch.setattr(rec,'async_list_recordings',reader)
 client=await hass_client()
 base='/api/cam_wise_bridge/api/recordings/'
 headers={'Authorization':'Bearer synthetic-recordings'}
 assert (await client.get(base+'camera.front')).status==401
 assert (await client.get(base+'camera.other',headers=headers)).status==403
 assert reader.await_count==0
 assert (await client.get(base+'camera.front',headers=headers)).status==200
 assert reader.await_count==1
 entry.runtime_data.client.async_status=AsyncMock(side_effect=CamWiseApiError('revoked'))
 assert (await client.get(base+'camera.front',headers=headers)).status==401
 assert reader.await_count==1

async def test_multiple_recording_cameras_explicitly_authorized(hass,hass_client,entry,api,monkeypatch):
 from homeassistant.setup import async_setup_component
 await async_setup_component(hass,'http',{})
 hass.config_entries.async_update_entry(entry,data={**entry.data,'pairing_token':'synthetic-multicam'},options={**entry.options,'recording_camera_entities':['camera.second','camera.third']})
 assert await hass.config_entries.async_setup(entry.entry_id)
 await hass.async_block_till_done()
 reader=AsyncMock(return_value={'recordings':[]})
 monkeypatch.setattr(rec,'async_list_recordings',reader)
 client=await hass_client();headers={'Authorization':'Bearer synthetic-multicam'}
 for entity in ('camera.front','camera.second','camera.third'):
  assert (await client.get('/api/cam_wise_bridge/api/recordings/'+entity,headers=headers)).status==200
 assert [call.args[2] for call in reader.await_args_list]==['camera.front','camera.second','camera.third']
 assert (await client.get('/api/cam_wise_bridge/api/recordings/camera.private',headers=headers)).status==403
 assert reader.await_count==3

@pytest.mark.parametrize('provider,before,after,title',[
 ('reolink','media-source://reolink/FILE|entry|0|sub|first-name|start|end1','media-source://reolink/FILE|entry|0|sub|final-name|start|end2','clip'),
 ('tapo_control','["20261028",100,124]','["20261028",100,131]','clip'),
])
async def test_growing_recording_has_stable_key_and_changed_revision(hass,provider,before,after,title):
 entry=NS(entry_id='cw');identity=('vendor','device','unique')
 a=rec._remember(hass,entry,'camera.a',provider,identity,before,title)
 b=rec._remember(hass,entry,'camera.a',provider,identity,after,title)
 assert a['key']==b['key'] and a['revision']!=b['revision'] and a['id']!=b['id']
 other=rec._remember(hass,entry,'camera.b',provider,('other','device2','unique2'),before,title)
 assert other['key']!=a['key']

async def test_cloud_signed_url_rotation_is_not_a_new_recording(hass):
 entry=NS(entry_id='cw');identity=('vendor','device','unique')
 a=rec._remember(hass,entry,'camera.a','blink',identity,'https://vendor.test/clip/123?token=old','same timestamp')
 b=rec._remember(hass,entry,'camera.a','blink',identity,'https://vendor.test/clip/123?token=new','same timestamp')
 assert a['key']==b['key'] and a['revision']==b['revision']

async def test_unifi_end_revision_changes_without_new_identity(hass):
 entry=NS(entry_id='cw');identity=('vendor','device','unique')
 a=rec._remember(hass,entry,'camera.a','unifiprotect',identity,'event123','clip','start:end1')
 b=rec._remember(hass,entry,'camera.a','unifiprotect',identity,'event123','clip','start:end2')
 assert a['key']==b['key'] and a['revision']!=b['revision']
