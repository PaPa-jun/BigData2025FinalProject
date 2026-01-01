const { createApp, ref, reactive } = Vue;

createApp({
    setup() {
        const searchQuery = ref('');
        const isLoading = ref(false);
        const hasSearched = ref(false);
        const error = ref(null);
        const processTime = ref(0);

        const searchResults = reactive({
            num: 0,
            items: []
        });

        const formatSize = (bytes) => {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        const setSearchQuery = (keyword) => {
            searchQuery.value = keyword;
            performSearch();
        };

        const getFileIcon = (filename) => {
            const extension = filename.split('.').pop().toLowerCase();
            const fileIcons = {
                'pdf': 'picture_as_pdf',
                'doc': 'article',
                'docx': 'article',
                'xls': 'table_chart',
                'xlsx': 'table_chart',
                'ppt': 'slideshow',
                'pptx': 'slideshow',
                'txt': 'text_snippet',
                'csv': 'table_view',
                'json': 'code',
                'xml': 'code',
                'html': 'web',
                'htm': 'web',
                'jpg': 'image',
                'jpeg': 'image',
                'png': 'image',
                'gif': 'image',
                'bmp': 'image',
                'mp4': 'movie',
                'avi': 'movie',
                'mkv': 'movie',
                'mp3': 'music_note',
                'wav': 'music_note',
                'zip': 'folder_zip',
                'rar': 'folder_zip',
                '7z': 'folder_zip',
                'tar': 'folder_zip',
                'gz': 'folder_zip',
                'default': 'insert_drive_file'
            };
            return fileIcons[extension] || fileIcons.default;
        };

        const getFileIconClass = (filename) => {
            const extension = filename.split('.').pop().toLowerCase();
            const iconClasses = {
                'pdf': 'file-pdf',
                'doc': 'file-word',
                'docx': 'file-word',
                'xls': 'file-excel',
                'xlsx': 'file-excel',
                'ppt': 'file-powerpoint',
                'pptx': 'file-powerpoint',
                'jpg': 'file-image',
                'jpeg': 'file-image',
                'png': 'file-image',
                'gif': 'file-image',
                'bmp': 'file-image',
                'mp4': 'file-video',
                'avi': 'file-video',
                'mkv': 'file-video',
                'mp3': 'file-audio',
                'wav': 'file-audio',
                'zip': 'file-zip',
                'rar': 'file-zip',
                '7z': 'file-zip',
                'tar': 'file-zip',
                'gz': 'file-zip',
                'txt': 'file-text',
                'csv': 'file-text',
                'json': 'file-code',
                'xml': 'file-code',
                'html': 'file-code',
                'htm': 'file-code',
                'default': ''
            };
            return iconClasses[extension] || iconClasses.default;
        };

        const buildDownloadUrl = async (hdfsPath) => {
            try {
                const path = hdfsPath.startsWith('/') ? hdfsPath : `/${hdfsPath}`;
                const response = await fetch('http://localhost:8000/api/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ path: path })
                });

                if (!response.ok) {
                    throw new Error(`Failed to retrieve download link: ${response.status} ${response.statusText}`);
                }
                const data = await response.json();

                return data.download_url;
            } catch (error) {
                console.error('Failed to obtain download URL:', error);
                return '#';
            }
        };

        const performSearch = async () => {
            if (!searchQuery.value.trim()) {
                error.value = '请输入搜索关键词';
                isLoading.value = false;
                return;
            }

            isLoading.value = true;
            error.value = null;
            hasSearched.value = true;
            processTime.value = 0;

            try {
                const startTime = Date.now();

                const response = await fetch('http://localhost:8000/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ query: searchQuery.value.trim() })
                });

                const endTime = Date.now();
                processTime.value = ((endTime - startTime) / 1000).toFixed(3);

                if (!response.ok) {
                    throw new Error(`Search failed: ${response.status} ${response.statusText}`);
                }

                const data = await response.json();

                searchResults.num = data.num || 0;
                searchResults.items = data.items || [];

                if (searchResults.num === 0) {
                    error.value = '未找到相关文件';
                }

            } catch (err) {
                console.error('Search request failed:', err);
                error.value = `搜索出现错误: ${err.message || '未知错误'}`;
            } finally {
                isLoading.value = false;
            }
        };

        const clearSearch = () => {
            searchQuery.value = '';
            searchResults.num = 0;
            searchResults.items = [];
            hasSearched.value = false;
            error.value = null;
        };

        const handleDownload = async (path, filename) => {
            try {
                const url = await buildDownloadUrl(path);
                if (url && url !== '#') {
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    setTimeout(() => {
                        document.body.removeChild(link);
                    }, 100);
                } else {
                    throw new Error('Unable to obtain a valid download link');
                }
            } catch (error) {
                console.error('Download failed:', error);
                alert(`下载失败: ${error.message || '请重试'}`);
            }
        };

        return {
            searchQuery,
            isLoading,
            hasSearched,
            error,
            processTime,
            searchResults,
            formatSize,
            setSearchQuery,
            getFileIcon,
            getFileIconClass,
            handleDownload,
            performSearch,
            clearSearch
        };
    },
    mounted() {
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        if (query) {
            this.searchQuery = query;
            this.performSearch();
        }
    }
}).mount('#app');