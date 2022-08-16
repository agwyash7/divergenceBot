from flask import jsonify, Response, request
from flask_restful import Resource

from models.pairs import Pairs
from models.globalSettings import GlobalSettings
from models.tests import Tests


class PairsApi(Resource):
    def get(self) -> Response:
        output = Pairs.objects()
        return jsonify({'result': output})

    def post(self) -> Response:
        data = request.get_json()
        post_activePair = Pairs(**data).save()
        output = {'id': str(post_activePair.id)}
        return jsonify({'result': output})


class PairApi(Resource):
    def get(self, pair_id: str):
        output = Pairs.objects.get(id=pair_id)
        return jsonify({'result': output})

    def put(self, pair_id: str):
        data = request.get_json()
        pair = Pairs.objects.get(id=pair_id)

        if data.get("isActive"):
            if data.get("isActive") == "false":
                pair.isActive = False
            elif data.get("isActive") == "true":
                pair.isActive = True

            pair.save()

        return jsonify({'result': pair})


class GlobalSettingsApi(Resource):
    def post(self) -> Response:
        data = request.get_json()
        post_globalsetting = GlobalSettings(**data).save()
        output = {'id': str(post_globalsetting.id)}
        return jsonify({'result': output})


class GlobalSettingApi(Resource):
    def get(self, globalsetting_id: str):
        output = GlobalSettings.objects.get(id=globalsetting_id)
        return jsonify({'result': output})


class TestsApi(Resource):
    def get(self) -> Response:
        output = Tests.objects()
        return jsonify({'result': output})


class TestApi(Resource):
    def get(self, pair_id: str):
        output = Tests.objects.get(id=pair_id)
        return jsonify({'result': output})
