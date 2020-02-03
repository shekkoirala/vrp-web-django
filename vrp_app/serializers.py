import os

from django.core.files.storage import FileSystemStorage
from rest_framework import serializers
from vrp_core.vrp import process

BYTES_50_MB = 52428800


def is_csv_file(file):
    return file.content_type.endswith('/csv') or file.name.endswith('.csv')


def is_csv_valid_size(file):
    return True if file.size <= BYTES_50_MB else False


def csv_is_valid(file):
    is_csv = file.content_type.endswith('/csv')
    valid_size = True if file.size / BYTES_50_MB < 1 else False
    return is_csv and valid_size


def validate_csv_file(file):
    message = None
    valid = True
    if not is_csv_file(file):
        message = 'The file uploaded is not in CSV format. Please upload csv file.'
        valid = False

    if not is_csv_valid_size(file):
        message ='The given file is greater than 50 MB. Please upload the file less than 50MB'
        valid = False
    return valid, message


class VRPSerializer(serializers.Serializer):
    csv_file = serializers.FileField(required=True)
    num_vehicle = serializers.IntegerField(required=True)
    depot = serializers.CharField(max_length=255, required=True)
    cols = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_csv_file(self, csv_file):
        is_valid_csv, message = validate_csv_file(csv_file)
        if not is_valid_csv:
            raise serializers.ValidationError(message)
        return csv_file

    def clean(self, data):
        self.is_valid(raise_exception=True)
        data = {k: v for k, v in data.items() if k in self.data}
        return data

    def save_csv(self, csv_file):
        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)

        uploaded_file_url = fs.url(filename)
        media_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        file_path = media_path + '/' + uploaded_file_url
        return file_path

    def parse(self, data):
        file_path = self.save_csv(data['csv_file'])
        response = process(file_path, int(data['num_vehicle']), str(data['depot']))
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print("The file does not exist")
        return response

    
    def download_csv(self, request):
        # fs = FileSystemStorage('/home/rosebay/Documents/test/vrp-web-django')
        from django.conf import settings
        fs = FileSystemStorage(settings.BASE_DIR)
        FileResponse(fs.open('result.csv', 'rb'), content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename="result.csv"'
        return response
