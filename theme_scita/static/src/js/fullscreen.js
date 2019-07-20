(function($) {

    var
        //屏幕高度
        SCREEN_HEIGHT = $(window).height(),

        //浏览器css3前缀
        FONTER = ['-webkit-', '-o-', '-moz-', '-ms-', ''],

        //定时器
        timer,
        //ua
        isChrome = /chrome/g.test(navigator.userAgent.toLowerCase());


    //判断是否是IE11以下
    var isIE = function() { //判断是否是低版本ie或者移动端，取消动画
        var flag = false,
            ua = navigator.userAgent,
            rv = -1,
            ieVer;

        if (!!window.ActiveXObject || "ActiveXObject" in window) { //IE10之前都有，IE11没有
            ieVer = /MSIE ([0-9]{1,}[\.0-9]{0,})/ig.exec(ua);
            isVer ? rv = parseFloat(isVer[1]) : rv = rv;
             rv >= 0 && rv <= 9 ? flag = true : flag = false;
        }
        return flag;
    }

    //不采用滚屏
    var noScroll = function() {
        this.dom.wrap.css('overflow', 'scroll');
        //删除导航
        this.dom.nav.remove();

        //设置默认高度
        this.dom.row.css('height', this.config.normalHeight);

        return 'noScroll';
    }

    //初始化dom
    var initEle = function() {

        var
            css = {}
            //设置高度
        this.dom.row.css('height', SCREEN_HEIGHT);

        for (var i = 0; i < FONTER.length; i++) {

            css[FONTER[i] + 'transition'] = FONTER[i] + 'transform ' + this.config.time + ' ' + this.config.type;
        }

        this.dom.move.css(css);
    }

    //运动函数
    var move = function(times) { //times存在且为1则代表是init里调用的move函数
        var
            i = 0,
            len = FONTER.length,
            //运动偏移量
            dis = -(this.status.currentNum - 1) * SCREEN_HEIGHT,

            //每屏节点样式
            obj = {},
            that = this,
            nav = this.dom.nav.children();

        //清除定时器
        clearTimeout(timer);
        //运动前fire事件
        this.fire('ready-scroll', 'pre', this.status.preNum, this.status.currentNum);

        for (; i < len; i++) {

            obj[FONTER[i] + 'transform'] = 'translate3d(0,' + dis + 'px,0)';
        }

        this.dom.move.css(obj);

        //nav添加class
        if(this.config.navClass){
           nav.removeClass(this.config.navClass);
           nav.eq(this.status.currentNum - 1).addClass(this.config.navClass);
        }

        //初始化调用move没有运动回调
        if (times) {
            return false
        }

        if (isChrome) {
            //chromecss3完成事件
            this.dom.move.on('webkitTransitionEnd', function() {
                $(this).off('webkitTransitionEnd');
                //完成运动事件
                that.fire('done-scroll', 'done', that.status.preNum, that.status.currentNum);
            });
        } else {
            //定时器动画完成fire"done-scroll"事件。
            timer = setTimeout(function() {
                //完成运动事件
                that.fire('done-scroll', 'done', that.status.preNum, that.status.currentNum);

            }, parseFloat(that.config.time) * 1000);
        }
    }

    //滚轮事件
    var scrollFn = function(e) {

        if (this.status.pause) return false;

        //如果两次滚动事件间隔小于动画时长返回
        if (Date.now() - this.config.then < parseFloat(this.config.time) * 1000 && this.config.then) return false;

        e = e || window.event;

        var dir = e.wheelDelta || e.detail;

        //兼容各个浏览器滚轮事件（苹果chrome）
        if (!isChrome) {
            dir % 120 === 0 ? dir = dir : dir = -dir;
        }

        //运动逻辑
        if (dir < 0) {
            if (this.status.currentNum === this.config.allNum) {
                return false;
            }
            this.status.preNum = this.status.currentNum++;

        } else {
            if (this.status.currentNum === 1) {
                return false;
            }
            this.status.preNum = this.status.currentNum--;

        }

        //运动函数
        move.call(screenScroll);
        //时间戳
        this.config.then = Date.now();

    };

    //点击事件
    var clickFn = function(num) {

        var that = this;
        this.status.preNum = this.status.currentNum;
        this.status.currentNum = num;

        //运动过程禁止滚轮事件
        this.status.pause = true;
        move.call(screenScroll);
        //打开滚轮事件
        setTimeout(function() {

            that.status.pause = false;

        }, parseFloat(that.config.time) * 1000);
    }

    //绑定事件
    var bind = function() {
        //滚轮事件
        if (document.addEventListener) {
            document.addEventListener('DOMMouseScroll', scrollFn.bind(screenScroll), false);
        }
        window.onmousewheel = document.onmousewheel = scrollFn.bind(screenScroll);

        //点击导航事件
        this.dom.nav.children().on('click', function() {

            clickFn.call(screenScroll,$(this).index() + 1)
        })
    }

    //主体
    var screenScroll = {
        //dom元素
        dom: {},
        //状态
        status: {},
        //配置
        config: {},
        init: function(param) {

            //运动节点
            if (param.move) {
                this.dom.move = $(param.move);
            } else {
                throw new Error('必须传入运动节点————move')
            }

            //导航节点
            if (param.nav) {
                this.dom.nav = $(param.nav);
            } else {
                throw new Error('必须传入导航节点————nav')
            }

            //每屏节点
            if (param.row) {
                this.dom.row = this.dom.move.find(param.row) || $(param.row);
            } else {
                throw new Error('必须传入每屏节点————row')
            }

            //外层包裹
            this.dom.wrap = param.wrap ? $(param.wrap) : $('body');

            //屏幕标号
            this.status.currentNum = 1;
            //屏幕上一屏标号
            this.status.preNum = 1;
            //暂停操作
            this.status.pause = false;

            //时间戳
            this.config.then = 0;

            //屏幕总数量
            this.config.allNum = param.allNum || this.dom.row.length;

            //不滚动屏幕时的默认高度
            this.config.normalHeight = param.normalHeight || 750;

            //滚屏时间
            this.config.time = param.time || '1s';

            //滚动效果
            this.config.type = param.type || 'ease';

            //navclass
            this.config.navClass = param.navClass || '';

            //最小高度
            this.config.minHeight = param.minHeight || 600;
            //不滚动
            if (isIE() || SCREEN_HEIGHT < this.config.minHeight) {

                //自定义事件传入noScroll信息
                this.fire('no-scroll', 'noScroll');

                
                //无滚动配置
                return noScroll.call(this);
            }
            //初始化dom
            initEle.call(this);

            //绑定事件
            bind.call(this);

            //运动move
            move.call(this, 1);
        },
        //禁止滚动
        pause: function() {
            this.status.pause = true;
            return this;
        },
        //打开滚动
        play: function() {
            this.status.pause = false;
            return this;
        },
        //改变运动属性，time和type
        changeMoveType:function(obj){

            //如果obj含有time和type以外的属性 则返回
            var 
                isLegel = Object.keys(obj).every(function(item,index,arr){
                    return item === 'time' || item === 'type';
                });

            if( !isLegel ){
                return false;
            }
            //改变属性
            $.extend(this.config,obj || {});

            //初始化运动元素
            initEle.call(this);
            return this;
        },
        //观察者模式监听函数
        on: function(eventType, listener) {

            if (!eventType || !listener) {
                return false;
            }

            if (!this._event) {
                this._event = {};
            }
            //保存监听函数
            if (!this._event[eventType]) {
                this._event[eventType] = {
                    'cache':[],
                    'listener':[]
                };
            }

            if (this._event[eventType]['listener'].indexOf(listener) < 0 && typeof listener === 'function') {
                this._event[eventType]['listener'].push(listener);
            }

            //如果有fire缓存数据，执行listener后删除数据
            if( this._event[eventType]['cache'].length !== 0){
                for (var i = 0; i < this._event[eventType]['listener'].length; i++) {
                    this._event[eventType]['listener'][i].call(this, this._event[eventType]['cache'].pop())
                }
            }
            return this;
        },

        //触发
        fire: function() {

            var
                eventType = arguments[0],
                param = Array.prototype.slice.call(arguments, 1) || [],
                index;

            //如果没有
            // if (!this._event || !this._event[eventType]) {
            //     return false;
            // }

            if( !this._event ){
                this._event = {}
            }

            if( !this._event[eventType] ){
                this._event[eventType] = {
                    //缓存数据，没有监听事件先触发fire的情况
                    'cache':[],
                    'listener':[]
                }
                //把数据推入缓存数组
                this._event[eventType]['cache'].push(param);
                //因为这是后并没有监听函数所以返回
                return 
            }
            //触发监听函数
            for (var i = 0; i < this._event[eventType]['listener'].length; i++) {
                this._event[eventType]['listener'][i].call(this, param)
            }
            return this;
        },

        //关闭
        off: function(evnetType, listener) {

            if (!this._event || !this._event[eventType]) {
                return false;
            }

            //如果只有事件类型，全部删除
            if (eventType && !listenser) {
                delete this._event[eventType];
            }

            if (eventType && listenser) {
                index = this._event[eventType]['listener'].indexOf(listener);
                if (index > 0) {
                    this._event[eventType]['listener'].splice(index, 1);
                }
            }

            return this;
        }

    }

    //注册jquery静态方法
    $.extend({
        FullScreen: function(param) {

            //初始化函数
            screenScroll.init(param);

            return screenScroll;
        }
    })

})(window.jQuery || window.Zepto)

