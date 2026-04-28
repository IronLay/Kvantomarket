$(function()
{
    let filter = $("[data-filter]");
    filter.on("click", function(event)
    {
        event.preventDefault();
        let cat = $(this).data('filter');

        if(cat == 'ALL')
            {
                $("[data-cat]").removeClass('hide');
            }
            else{
                $("[data-cat]").each(function(){

                    let workCat = $(this).data('cat');
                    console.log(workCat);
        
                    if(workCat != cat)
                        {
                            $(this).addClass('hide');
                        }
                        else{
                            $(this).removeClass('hide');
                        }
        
                });
            }
        

        
    });




    /*525252525252525*/
    const modalCall = $("[data-modal]");
    const modalClose = $("[data-close]");
    modalCall.on("click", function(event)
    {
        event.preventDefault();
        let $this = $(this);

        let modalId = $(this).data('modal');
        $(modalId).addClass('show');
        $("body").addClass('no-scroll');
        console.log(modalId);
    });

    modalClose.on("click", function(event)
    {
        event.preventDefault();
        let $this = $(this);

        let modalParent = $(this).parents('.modals');
        modalParent.removeClass('show');
        $("body").removeClass('no-scroll');

        console.log(modalId);
    });


});