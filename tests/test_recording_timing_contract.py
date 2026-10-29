"""Typed UTC metadata and fail-closed vendor timing; no real camera access."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
import pytest
from homeassistant.helpers import entity_registry as er
from custom_components.cam_wise import recordings as rec, recording_providers as pro

@pytest.mark.parametrize('value',[None,True,float('nan'),float('inf'),'today','2026-10-28T10:00:00',datetime(2026,10,28)])
def test_missing_or_ambiguous_time_is_not_guessed(value):
    assert rec.timing(value,completed=True)['captured_at'] is None
    assert not rec.timing(value,completed=True)['completed']


def test_timing_normalizes_aware_vendor_time():
    value=datetime(2026,10,28,10,tzinfo=timezone(timedelta(hours=2)))
    assert rec.timing(value,completed=True)=={'captured_at':value.timestamp(),'ended_at':None,'completed':True}


async def test_ring_metadata_matches_exact_video_and_ready_status(hass,monkeypatch):
    row=er.async_get(hass).async_get_or_create('camera','ring','synthetic-timed')
    hass.states.async_set(row.entity_id,'idle',{'last_video_id':123,'video_url':'https://secret.test'})
    event={'id':123,'created_at':'2026-10-28T10:00:00Z','recording':{'status':'ready'}}
    monkeypatch.setattr(pro,'entity',lambda *a:NS(_last_event=event))
    result=await rec.async_list_recordings(hass,NS(entry_id='cw'),row.entity_id)
    record=result['recordings'][0]
    assert record['captured_at']==datetime(2026,10,28,10,tzinfo=timezone.utc).timestamp()
    assert record['completed'] and 'secret.test' not in str(result)
    event['id']=999
    assert not rec._ring_timing(hass,row.entity_id,123)['captured_at']
    event['id']=123;event['recording']['status']='processing'
    assert not rec._ring_timing(hass,row.entity_id,123)['completed']


async def test_blink_times_are_sorted_by_desktop_not_labels(hass,monkeypatch):
    api=NS(recent_clips=[{'clip':'https://vendor.test/a','time':'2026-10-28T10:00:00Z'}],
           clip=None,sync=NS(urls=NS(base_url='https://vendor.test')))
    monkeypatch.setattr(pro,'entity',lambda *a:NS(_camera=api))
    row=(await pro.list_sources(hass,NS(platform='blink'),'camera.selected'))[0]
    assert row[3]['completed'] and isinstance(row[3]['captured_at'],float)
    api.recent_clips[0]['time']='unparseable'
    assert (await pro.list_sources(hass,NS(platform='blink'),'camera.selected'))[0][3]['captured_at'] is None


def test_reolink_uses_device_timezone_and_end(hass,monkeypatch):
    from homeassistant.components.reolink import util
    monkeypatch.setattr(util,'get_host',lambda *a:NS(api=NS(timezone=lambda:timezone(timedelta(hours=2)))))
    data=rec._reolink_timing(hass,'entry','media-source://reolink/FILE|entry|0|sub|file|20261028100000|20261028100100')
    assert data['captured_at']==datetime(2026,10,28,8,tzinfo=timezone.utc).timestamp()
    assert data['ended_at']-data['captured_at']==60 and data['completed']
    monkeypatch.setattr(util,'get_host',lambda *a:NS(api=NS(timezone=lambda:None)))
    assert rec._reolink_timing(hass,'entry','source')['captured_at'] is None



def test_tapo_requires_explicit_device_offset():
    assert pro._tapo_timing({},1000,1100)['captured_at'] is None
    assert pro._tapo_timing({'timezoneOffset':True},1000,1100)['captured_at'] is None
    assert pro._tapo_timing({'timezoneOffset':3600},10000,10100)=={
        'captured_at':6400.0,'ended_at':6500.0,'completed':True}
