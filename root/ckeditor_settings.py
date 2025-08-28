CKEDITOR_5_ALLOW_ALL_FILE_TYPES = True
CKEDITOR_5_UPLOAD_FILE_TYPES = ['jpeg', 'pdf', 'png', 'jpg', 'pdf', 'xlsx', 'xls', 'docx']  # optional

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': {
            'items': [
                'undo', 'redo', '|', 'selectAll', 'findAndReplace', '|', 'heading', '|', 'fontSize', 'fontColor',
                'fontBackgroundColor', '|', 'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript',
                'highlight', '|', 'link', 'insertImage', 'mediaEmbed', 'fileUpload', 'insertTable', '|',
                'blockQuote', 'specialCharacters', 'horizontalLine', '|', 'alignment', 'bulletedList', 'numberedList',
                'outdent', 'indent', 'removeFormat', '|', 'sourceEditing'
                # 'sourceEditing'ni olib tashlang, agar kerak bo'lmasa
            ],
            'shouldNotGroupWhenFull': True
        },
        'fontSize': {
            'options': [10, 12, 14, 'default', 18, 20, 22],
            'supportAllValues': True
        },
        'heading': {
            'options': [
                # Heading sozlamalarini cheklash yoki o'zgartirish
            ]
        },
        'htmlSupport': {
            'allow': [
                {
                    'name': '/^.*$/',
                    'styles': True,
                    'attributes': True,
                    'classes': True
                }
            ],
            'disallow': [
                {
                    'styles': {
                        '/^background.*$/': True,  # Faqat kerakli background style'larini ruxsat etish
                    },
                    'attributes': {
                        '/^on.*$/': True  # JavaScript atributlarini o'chirish
                    }
                }
            ]
        },
        'image': {
            'toolbar': [
                'toggleImageCaption', 'imageTextAlternative', '|', 'imageStyle:inline', 'imageStyle:wrapText',
                'imageStyle:breakText', '|', 'resizeImage'
            ]
        },
        'link': {
            'addTargetToExternalLinks': True,
            'defaultProtocol': 'https://',
            'decorators': {
                'toggleDownloadable': {
                    'mode': 'manual',
                    'label': 'Downloadable',
                    'attributes': {
                        'download': 'file'
                    }
                }
            }
        },
        'list': {
            'properties': {
                'styles': True,
                'startIndex': True,
                'reversed': True
            }
        },
        'placeholder': 'Type something',
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties']
        },
    }
}

CKEDITOR_5_MAX_FILE_SIZE = 100
