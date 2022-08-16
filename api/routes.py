from api.pairController import PairsApi, PairApi, GlobalSettingsApi, GlobalSettingApi, TestsApi, TestApi


def create_routes(api):
    api.add_resource(PairsApi, '/pair/')
    api.add_resource(PairApi, '/pair/<pair_id>')

    api.add_resource(TestsApi, '/test/')
    api.add_resource(TestApi, '/test/<pair_id>')

    api.add_resource(GlobalSettingsApi, '/globalSetting/')
    api.add_resource(GlobalSettingApi, '/globalSetting/<globalsetting_id>')